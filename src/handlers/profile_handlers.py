"""Provides profile control panel handlers for the Tornado app.

UploadHandler and DownloadHandler handle the file uploads and downloads respectively.
ProfileHandler shows the profile bio including the files, and handles the changes to bio."""

from base_handler import *
from preprocessing.crawler import pdf2txt

from tornado import web
from tornado import escape
from tornado import gen
from tornado.escape import json_encode
from gridfs.errors import NoFile
from pymongo.errors import OperationFailure

import os
import motor
import random
import string
import re
from requests.utils import quote
from time import strftime
import datetime
import pytz
from pytz import timezone
from bson import json_util
import warnings

__author__ = "Arttu Modig"
__license__ = "MIT"
__version__ = "0.1"
__maintainer__ = "Arttu Modig"
__email__ = "arttu.modig@gmail.com"
__status__ = "Prototype"


class BaseProfileHandler(BaseHandler):
    def initialize(self):
        """Tornado handler initialization"""
        self.file_param_name = 'files'
        self.access_control_allow_origin = '*'
        self.access_control_allow_credentials = False
        self.access_control_allow_methods = ['OPTIONS', 'HEAD', 'GET', 'POST', 'PUT', 'PATCH', 'DELETE']
        self.access_control_allow_headers = ['Content-Type', 'Content-Range', 'Content-Disposition']
        self.timezone = timezone('Europe/Helsinki')

    def get_download_url(self, filename=None, key=None):
        if filename:
            url = self.request.host + '/download' + '?file=' + escape.url_escape(filename)
        elif key:
            url = self.request.host + '/download' + '?key=' + escape.url_escape(key)
        else:
            raise web.HTTPError(500)
        return url

    def send_access_control_headers(self):
        """Set access control HTTP headers"""
        self.set_header('Access-Control-Allow-Origin', self.access_control_allow_origin)
        self.set_header('Access-Control-Allow-Credentials',
                        'true' if self.access_control_allow_credentials else 'false')
        self.set_header('Access-Control-Allow-Methods', ', '.join(self.access_control_allow_methods))
        self.set_header('Access-Control-Allow-Headers', ', '.join(self.access_control_allow_headers))

    def send_content_type_header(self):
        """Set content type HTTP header"""
        self.set_header('Vary', 'Accept')
        if 'application/json' in self.get_server_vars('HTTP_ACCEPT'):
            self.set_header('Content-type', 'application/json')
        else:
            self.set_header('Content-type', 'text/plain')

    def get_server_vars(self, _id):
        """Returns a list of header values given a header name"""
        return self.request.headers.get_list(_id)

    def head(self):
        """Set default HTTP header"""
        self.set_header('Pragma', 'no-cache')
        self.set_header('Cache-Control', 'no-store, no-cache, must-revalidate')
        self.set_header('Content-Disposition', 'inline; filename="files.json"')
        # Prevent Internet Explorer from MIME-sniffing the content-type:
        self.set_header('X-Content-Type-Options', 'nosniff')
        if self.access_control_allow_origin:
            self.send_access_control_headers()
        self.send_content_type_header()


class DownloadHandler(BaseProfileHandler):
    """A Tornado handler for file download"""

    @staticmethod
    def fid(file_id=None, filename=None):
        """Make a file ID either from original ID or filename"""
        if not file_id:
            if not filename:
                raise web.HTTPError(500)
            else:
                fid = filename
        else:
            fid = file_id
        return fid

    @gen.coroutine
    def get_grid_out(self, file_id=None, filename=None):
        """Get GridOut object from MongoDB's GridFS file system"""
        fs = motor.MotorGridFS(self.application.db, collection=u'fs')
        fid = self.fid(file_id, filename)
        try:
            grid_out = yield fs.get(fid)
        except NoFile:
            raise web.HTTPError(404)
        if filename:
            assert grid_out.filename is filename, "file names does not match!"
        raise gen.Return(grid_out)

    @web.authenticated
    @gen.coroutine
    def get(self):
        """Fetch a file from MongoDB's GridFS and send it to UploadHandler"""
        print "GET download"
        # use either filename or file key
        filename = self.get_argument('file', default=None)
        key = self.get_argument('key', default=None)
        # get a GridFS GridOut object
        grid_out = yield self.get_grid_out(file_id=key, filename=filename)
        # Prevent browsers from MIME-sniffing the content-type:
        self.set_header('X-Content-Type-Options', 'nosniff')
        self.set_header('Content-Type', 'application/octet-stream')
        # self.set_header('Content-Type', grid_out.content_type)
        self.set_header('Content-Disposition', 'attachment; filename=%s' % grid_out.filename)
        self.set_header('Content-Length', grid_out.length)
        self.set_header('Upload-Date', grid_out.upload_date.strftime('%A, %d %M %Y %H:%M:%S %Z'))
        # stream the file content to RequestHandler
        yield grid_out.stream_to_handler(self)


class UploadHandler(BaseProfileHandler):
    """A Tornado handler for file upload"""

    # upload attributes
    MIN_FILE_SIZE = 1  # bytes
    MAX_FILE_SIZE = 5000000  # bytes
    DOCUMENT_TYPES = re.compile('application/pdf')  # re.compile('image/(gif|p?jpeg|(x-)?png)')
    ACCEPT_FILE_TYPES = DOCUMENT_TYPES

    def callback(self, result, error):
        if error:
            raise error
        print 'result', repr(result)
        IOLoop.instance().stop()

    def validate(self, f):
        """Validate a given file (a dictionary object)."""
        if f['size'] < self.MIN_FILE_SIZE:
            f['error'] = 'File is too small'
        elif f['size'] > self.MAX_FILE_SIZE:
            f['error'] = 'File is too big'
        elif not self.ACCEPT_FILE_TYPES.match(f['type']):
            f['error'] = 'File type not allowed'
        else:
            return True
        return False

    @staticmethod
    def get_file_size(f):
        f.seek(0, 2)  # Seek to the end of the file
        size = f.tell()  # Get the position of EOF
        f.seek(0)  # Reset the file position to the beginning
        return size

    @gen.coroutine
    def write_file(self, file_content, user, key, result):
        """Write file to MongoDB's GridFS system."""
        fs = motor.MotorGridFS(self.application.db, collection=u'fs')
        # default: file_id is the ObjectId of the resulting file
        file_id = yield fs.put(file_content, _id=key, user=user,
                               filename=result['name'], content_type=result['type'],
                               title=result['title'], abstract=result['abstract'])
        assert file_id is key, "file_id is not key (%r): %r" % (key, file_id)

    def handle_upload_db(self):
        """Handle uploads to database. Files are buffered into memory.
        :return JSON list of uploaded files.
        """
        def _extract_abstract(body, content_type):
            p = re.compile('pdf')
            if not p.search(content_type):
                warnings.warn("The file was not PDF.")
                return "Not a PDF!"
            # save PDF temp file
            temp_path = "uploads/temp.pdf"
            temp_file = open(temp_path, 'w')
            temp_file.write(body)
            temp_file.close()
            # convert and write ASCII to temp file
            pdf2txt.main(["scriptname", "-o", "uploads/output.txt", temp_path])
            out = open("uploads/output.txt", 'r')
            contents = out.read()
            out.close()
            # find and return abstract
            abstract_start_position = contents.lower().find("abstract")
            abstract_end_position = contents[abstract_start_position:].lower().find("\n\n") + abstract_start_position
            len_abstract = len("abstract") + len('\n')
            return re.sub('\s+', ' ', contents[abstract_start_position + len_abstract:abstract_end_position]).strip()

        results = []
        if self.request.files:
            # each f is a dictionary
            for (f, title) in zip(self.request.files[self.file_param_name], self.get_arguments('title[]')):
                result = {}
                result['name'] = f['filename']
                file_body = f['body']
                result['title'] = title
                result['type'] = f['content_type']
                result['size'] = len(file_body)
                if self.validate(result):
                    user = self.get_current_user()
                    key = ''.join(random.choice(string.ascii_lowercase + string.digits) for x in range(6))
                    # Abstract extraction requires that the file is stored physically i.e. a file path
                    result['abstract'] = _extract_abstract(file_body, f['content_type'])
                    # Write file to database
                    self.write_file(file_body, user, key, result)
                    # Set additional fields for File Upload plugin
                    result['deleteType'] = 'DELETE'
                    result['key'] = key
                    result['deleteUrl'] = self.request.uri + '?key=' + key
                    if 'url' not in result:
                        result['url'] = self.get_download_url(key=key)
                    if self.access_control_allow_credentials:
                        result['deleteWithCredentials'] = True
                    result['uploadDate'] = datetime.datetime.now(self.timezone).strftime('%Y-%m-%d %H:%M')
                results.append(result)
        return results

    # def handle_upload_dir(self):
    #     results = []
    #     if self.request.files[self.file_param_name]:
    #         for f in self.request.files[self.file_param_name]:
    #             result = {}
    #             result['name'] = f['filename']
    #             result['type'] = f['content_type']
    #             result['size'] = self.get_file_size(f)
    #             if self.validate(result):
    #                 extension = os.path.splitext(f['filename'])[1]
    #                 f_name = ''.join(random.choice(string.ascii_lowercase + string.digits) for x in range(6))
    #                 final_filename = f_name + extension
    #                 output_file = open("uploads/" + final_filename, 'w')
    #                 output_file.write(f['body'])
    #             results.append(result)
    #     return results


    @web.authenticated
    def get(self):
        self.redirect("/control")

    @web.authenticated
    @web.asynchronous
    def post(self):
        """Receives POST arguments/files, or deletes a file"""
        if self.get_argument('_method', default=None) == 'DELETE':
            return self.delete()
        result = {'files': self.handle_upload_db()}
        s = json.dumps(result, separators=(',', ':'))
        redirect = self.get_argument('redirect', default=None)
        if redirect:
            return self.redirect(str(redirect.replace('%s', quote(s, ''), 1)))
        if 'application/json' in self.request.headers.get_list('Accept'):
            self.request.set_headers('Content-Type', 'application/json')
        print "POST writing: %s" % s
        self.write(s)
        self.finish()

    @web.authenticated
    @gen.coroutine
    def delete(self):
        """Delete a file in the database"""
        key = self.get_argument('key', default=None) or ''
        fs = motor.MotorGridFS(self.application.db, collection=u'fs')
        # get file name
        grid_out = yield fs.get(key)
        filename = grid_out.filename
        # delete a file with the key
        yield fs.delete(key)
        # make JSON response
        s = json.dumps({'files': {filename: True}}, separators=(',', ':'))
        if 'application/json' in self.request.headers.get_list('Accept'):
            self.request.set_headers['Content-Type'] = 'application/json'
        print "DELETE writing: %s" % s
        self.write(s)


class ProfileHandler(BaseProfileHandler):
    @gen.coroutine
    def get_user_email(self, user):
        doc = yield self.application.db['users'].find_one({'user': user})
        email = doc['email']
        raise gen.Return(email)

    @gen.coroutine
    def get_user_name(self, user):
        doc = yield self.application.db['users'].find_one({'user': user})
        name = doc['name']
        raise gen.Return(name)

    @gen.coroutine
    def get_files_db(self, user):
        """Finds all files by selected user.
        :return a list of file dictionaries (can be empty).
        """
        files = []
        fs = motor.MotorGridFS(self.application.db, collection=u'fs')
        cursor = fs.find({"user": user}, timeout=False)
        while (yield cursor.fetch_next):
            file = {}
            grid_out = cursor.next_object()
            # content = yield grid_out.read()
            try:
                file['title'] = grid_out.title
            except AttributeError:
                file['title'] = "[No title]"
            file['name'] = grid_out.filename
            file['key'] = grid_out._id
            file['size'] = grid_out.length
            file['type'] = grid_out.content_type
            # grid returns a datetime.datetime
            upload_date = grid_out.upload_date.replace(tzinfo=pytz.utc).astimezone(self.timezone)
            file['uploadDate'] = upload_date.strftime('%Y-%m-%d %H:%M')
            file['deleteType'] = 'DELETE'
            file['deleteUrl'] = self.request.uri + '?key=' + file['key']
            file['url'] = self.get_download_url(key=file['key'])
            if self.access_control_allow_credentials:
                file['deleteWithCredentials'] = True
            files.append(file)
        raise gen.Return(files)

    @gen.coroutine
    def get_bio(self, user):
        """Get user's profile bio"""
        # find user document
        user = yield self.application.db['users'].find_one({'user': user})
        if user is None:
            raise web.HTTPError(500)
        try:
            bio = user['bio']
        except KeyError:
            raise gen.Return("Empty bio")  # return empty string if no bio
        else:
            raise gen.Return(bio)

    @gen.coroutine
    def update_bio(self, bio_string):
        """Update profile bio"""
        username = self.get_current_user()
        # find user document
        user = yield self.application.db['users'].find_one({'user': username})
        _id = user['_id']
        # set new bio with update modifier $set
        try:
            yield self.application.db['users'].update({'_id': _id}, {'$set': {'bio': bio_string}})
        except OperationFailure:
            raise web.HTTPError(500)

    @web.authenticated
    @gen.coroutine
    def get(self):
        """GET JSON response with profile info, including personal files"""
        username = self.get_current_user()
        email = yield self.get_user_email(username)
        files = yield self.get_files_db(username)
        bio = yield self.get_bio(username)
        # use BSON util for default date conversion
        s = json.dumps(files, separators=(',', ':'), default=json_util.default)
        response = {'user': username, 'email': email, 'bio': bio, 'files': s}
        # write a JSON response
        self.write(response)  # written as JSON automatically

    @web.authenticated
    @gen.coroutine
    def post(self):
        """Gets REQUEST data containing the new bio"""
        payload = json.loads(self.request.body)
        if 'bio_new_text' in payload:
            yield self.update_bio(payload['bio_new_text'])
            print "Updated bio"
            self.write({"msg": "Bio saved"})
        else:
            print "didn't find bio_new_text"


class ProfileIndexHandler(BaseProfileHandler):
    @web.authenticated
    def get(self):
        # Old style, send template variables
        variables = {'user': "foobar", 'email': "email@email.com", 'bio': "short bio", 'files': json.dumps({})}
        self.render("control.html", **variables)


class UpdateKeyWordsHandler(BaseProfileHandler):
    pass
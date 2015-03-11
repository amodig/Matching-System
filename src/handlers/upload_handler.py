import os
import json
import magic
import motor
import random
import string
import re
from tornado import web
from tornado import escape
from tornado import gen
from requests.utils import quote
from time import strftime
from base_handler import *

from gridfs.errors import NoFile

class UploadHandler(BaseHandler):

    # class attributes
    MIN_FILE_SIZE = 1  # bytes
    MAX_FILE_SIZE = 5000000  # bytes
    DOCUMENT_TYPES = re.compile("application/pdf")  # re.compile('image/(gif|p?jpeg|(x-)?png)')
    ACCEPT_FILE_TYPES = DOCUMENT_TYPES

    def initialize(self):
        self.file_param_name = 'files'
        self.access_control_allow_origin = '*'
        self.access_control_allow_credentials = False
        self.access_control_allow_methods = ['OPTIONS', 'HEAD', 'GET', 'POST', 'PUT', 'PATCH', 'DELETE']
        self.access_control_allow_headers = ['Content-Type', 'Content-Range', 'Content-Disposition']

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
    def get_file_size(file):
        file.seek(0, 2)  # Seek to the end of the file
        size = file.tell()  # Get the position of EOF
        file.seek(0)  # Reset the file position to the beginning
        return size

    @staticmethod
    def fid(file_id=None, filename=None):
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
        fs = motor.MotorGridFS(self.application.db, collection=u'fs')
        fid = self.fid(file_id, filename)
        try:
            grid_out = yield fs.get(fid)
        except NoFile:
            raise web.HTTPError(404)
        if filename:
            assert grid_out.filename is filename, "file names does not match!"
        raise gen.Return(grid_out)

    @gen.coroutine
    def write_file(self, file_content, key, result):
        """Write file to MongoDB GridFS system."""
        fs = motor.MotorGridFS(self.application.db, collection=u'fs')
        # default: file_id is the ObjectId of the resulting file
        file_id = yield fs.put(file_content, _id=key, filename=result['name'],
                               content_type=result['type'])
        assert file_id is key, "file_id is not key (%r): %r" % (key, file_id)

    def get_download_url(self, filename=None, key=None):
        if filename:
            url = self.request.uri + '?file=' + escape.url_escape(filename)
        elif key:
            url = self.request.uri + '?key=' + escape.url_escape(key)
        else:
            raise web.HTTPError(500)
        return url + '&download=1'

    def handle_upload_db(self):
        """Handle uploads to database.
        :return JSON list of uploaded files.
        """
        results = []
        if self.request.files:
            # each f is a dictionary
            for f in self.request.files[self.file_param_name]:
                result = {}
                result['name'] = f['filename']
                file_body = f['body']
                result['type'] = f['content_type']
                result['size'] = len(file_body)
                if self.validate(result):
                    key = ''.join(random.choice(string.ascii_lowercase + string.digits) for x in range(6))
                    self.write_file(file_body, key, result)
                    result['deleteType'] = 'DELETE'
                    result['key'] = key
                    result['deleteUrl'] = self.request.uri + '?key=' + key
                    if 'url' not in result:
                        result['url'] = self.get_download_url(key=key)
                    if self.access_control_allow_credentials:
                        result['deleteWithCredentials'] = True
                results.append(result)
        return results

    def handle_upload_dir(self):
        results = []
        if self.request.files[self.file_param_name]:
            for f in self.request.files[self.file_param_name]:
                result = {}
                result['name'] = f['filename']
                result['type'] = magic.from_file(f, mime=True)
                result['size'] = self.get_file_size(f)
                if self.validate(result):
                    extension = os.path.splitext(f['filename'])[1]
                    f_name = ''.join(random.choice(string.ascii_lowercase + string.digits) for x in range(6))
                    final_filename = f_name + extension
                    output_file = open("uploads/" + final_filename, 'w')
                    output_file.write(f['body'])
                results.append(result)
        return results

    @gen.coroutine
    def do_download(self):
        # use either filename or file key
        filename = self.get_argument('file', default=None)
        key = self.get_argument('key', default=None)
        # get a GridFS GridOut object
        grid_out = yield self.get_grid_out(file_id=key, filename=filename)
        # Prevent browsers from MIME-sniffing the content-type:
        self.set_header('X-Content-Type-Options', 'nosniff')
        self.set_header('Content-Type', 'application/octet-stream')
        #self.set_header('Content-Type', grid_out.content_type)
        self.set_header('Content-Disposition', 'attachment; filename=%s' % grid_out.filename)
        self.set_header('Content-Length', grid_out.length)
        self.set_header('Upload-Date', grid_out.upload_date.strftime('%A, %d %M %Y %H:%M:%S %Z'))
        # stream the file content to RequestHandler
        yield grid_out.stream_to_handler(self)
        self.finish()

    def send_access_control_headers(self):
        self.set_header('Access-Control-Allow-Origin', self.access_control_allow_origin)
        self.set_header('Access-Control-Allow-Credentials',
                        'true' if self.access_control_allow_credentials else 'false')
        self.set_header('Access-Control-Allow-Methods', ', '.join(self.access_control_allow_methods))
        self.set_header('Access-Control-Allow-Headers', ', '.join(self.access_control_allow_headers))

    def send_content_type_header(self):
        self.set_header('Vary', 'Accept')
        if 'application/json' in self.get_server_vars('HTTP_ACCEPT'):
            self.set_header('Content-type', 'application/json')
        else:
            self.set_header('Content-type', 'text/plain')

    def get_server_vars(self, _id):
        """Returns a list of header values given a header name."""
        return self.request.headers.get_list(_id)

    def head(self):
        self.set_header('Pragma', 'no-cache')
        self.set_header('Cache-Control', 'no-store, no-cache, must-revalidate')
        self.set_header('Content-Disposition', 'inline; filename="files.json"')
        # Prevent Internet Explorer from MIME-sniffing the content-type:
        self.set_header('X-Content-Type-Options', 'nosniff')
        if self.access_control_allow_origin:
            self.send_access_control_headers()
        self.send_content_type_header()

    @web.asynchronous
    def get(self):
        if self.get_argument('download', default=None):
            return self.do_download()
        template_vars = {}
        self.render("control.html", **template_vars)

    @web.asynchronous
    def post(self):
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

    @gen.coroutine
    def delete(self):
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

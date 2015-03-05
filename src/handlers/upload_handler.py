import os
import json
import magic
import motor
import random
import string
import re

from tornado.web import asynchronous
from tornado.gen import coroutine
from tornado.ioloop import IOLoop
from tornado.options import define, options
from requests.utils import quote

from base_handler import *

class UploadHandler(BaseHandler):

    # class attributes
    MIN_FILE_SIZE = 1  # bytes
    MAX_FILE_SIZE = 5000000  # bytes
    DOCUMENT_TYPES = re.compile('application/pdf')  #re.compile('image/(gif|p?jpeg|(x-)?png)')
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
        IOLoop.instance().stop(self)

    def validate(self, file):
        """Validate a given file (a dictionary object)."""
        if file['size'] < self.MIN_FILE_SIZE:
            file['error'] = 'File is too small'
        elif file['size'] > self.MAX_FILE_SIZE:
            file['error'] = 'File is too big'
        elif not self.ACCEPT_FILE_TYPES.match(file['type']):
            file['error'] = 'File type not allowed'
        else:
            return True
        return False

    @staticmethod
    def get_file_size(file):
        file.seek(0, 2)  # Seek to the end of the file
        size = file.tell()  # Get the position of EOF
        file.seek(0)  # Reset the file position to the beginning
        return size

    @tornado.gen.coroutine
    def write_file(self, file_content, key, result):
        """Write file to MongoDB GridFS system."""
        fs = motor.MotorGridFS(self.application.db['documents'])
        # default: file_id is the ObjectId of the resulting file
        file_id = yield fs.put(file_content, _id=key, callback=self.callback, filename=result['name'],
                               content_type=result['type'])
        # start IOLoop when callback has run
        IOLoop.instance().start(self)
        assert id == file_id

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
                print result['name']  # debug
                filebody = f['body']
                # result['type'] = magic.from_file(filebody, mime=True)  # get MIME type
                result['type'] = f['content_type']
                # result['size'] = self.get_file_size(filebody)
                result['size'] = len(filebody)
                if self.validate(result):
                    key = ''.join(random.choice(string.ascii_lowercase + string.digits) for x in range(6))
                    #document = {key : f}
                    #self.application.db['documents'].insert(document, callback=self.callback)
                    #self.write_file(filebody, key, result)
                    result['deleteType'] = 'DELETE'
                    result['key'] = key
                    result['deleteUrl'] = self.request.full_url() + '/?key=' + key
                    if 'url' not in result:
                        result['url'] = self.request.full_url() + '/' + key + '/' + quote(result['name'].encode('utf-8'))
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

    def download(self):
        pass  # TODO

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

    def get(self):
        if self.get_query_argument('download', default=None):
            return self.download()

        template_vars = {}
        self.render("control.html", **template_vars)

    @tornado.web.asynchronous
    def post(self):

        if self.get_query_argument('_method', default=None) == 'DELETE':
            return self.delete()
        result = {'files': self.handle_upload_db()}
        s = json.dumps(result, separators=(',', ':'))
        redirect = self.get_query_argument('redirect', default=None)
        if redirect:
            return self.redirect(str(redirect.replace('%s', quote(s, ''), 1)))
        if 'application/json' in self.request.headers.get_list('Accept'):
            self.request.set_headers('Content-Type', 'application/json')
        print "kirjoitetaan %s" % s
        self.write(s)
        print "POST files:"
        print [f['filename'] for f in self.request.files[self.file_param_name]]
        print "POST arguments:"
        print self.request.arguments

        print 'FINISHING'
        self.finish()

    @tornado.gen.coroutine
    def delete(self):
        key = self.request.get('key') or ''
        print key
        fs = motor.MotorGridFS(self.application.db['documents'])
        yield fs.delete(key, callback=self.callback)
        # start IOLoop when callback has run
        IOLoop.instance().start(self)
        s = json.dumps({key: True}, separators=(',', ':'))
        if 'application/json' in self.request.headers.get('Accept'):
            self.request.headers['Content-Type'] = 'application/json'
        self.request.connection.write(s)
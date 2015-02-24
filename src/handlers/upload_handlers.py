import os

__author__ = 'amodig'

import json
import magic
import motor
import random
import string

from base_handler import *

MONGO_SERVER = 'localhost' # client = motor.MotorClient(MONGO_SERVER, 27017)
MIN_FILE_SIZE = 1  # bytes
MAX_FILE_SIZE = 5000000  # bytes
DOCUMENT_TYPES = 'application/pdf' #re.compile('image/(gif|p?jpeg|(x-)?png)')
ACCEPT_FILE_TYPES = DOCUMENT_TYPES

class S3PhotoUploadHandler(BaseHandler):
    """ Ideally image resizing should be done with a queue and a seperate python process """
    def get(self):
        template_vars = {}

        self.render('upload.html', **template_vars)

    @tornado.web.asynchronous
    def post(self):
        file1 = self.request.files['file1'][0]
        img = cStringIO.StringIO(file1['body'])
        image = Image.open(img)

        thread = threading.Thread(target=self.resize_the_image, args=(image,))
        thread.start()

    def resize_the_image(self, image):
        im2 = image.resize((100, 100), Image.NEAREST)
        out_im2 = cStringIO.StringIO()
        im2.save(out_im2, 'PNG')
        tornado.ioloop.IOLoop.instance().add_callback(functools.partial(self.upload_to_s3, out_im2))

    def upload_to_s3(self, image2):
        AWS_ACCESS_KEY_ID = ''
        AWS_SECRET_ACCESS_KEY = ''

        # credentials can be stored in environment AWS_ACCESS_KEY_ID and AWS_SECRET_ACCESS_KEY
        conn = boto.connect_s3(AWS_ACCESS_KEY_ID, AWS_SECRET_ACCESS_KEY)

        # Connect to bucket and create key
        b = conn.get_bucket('photos')
        k = b.new_key('example5.png')

        # Note we're setting contents from the in-memory string provided by cStringIO
        k.set_contents_from_string(image2.getvalue(), headers={"Content-Type": "image/png"})
        tornado.ioloop.IOLoop.instance().add_callback(functools.partial(self.image_uploaded))

    def image_uploaded(self):
        self.set_secure_cookie('flash', "File Uploaded")
        self.redirect("/")


class UploadHandler(BaseHandler):
    def get(self):
        self.render("upload-files.html")


class PdfUploader(BaseHandler):

    def validate(self, file):
        if file['size'] < MIN_FILE_SIZE:
            file['error'] = 'File is too small'
        elif file['size'] > MAX_FILE_SIZE:
            file['error'] = 'File is too big'
        elif not ACCEPT_FILE_TYPES.match(file['type']):
            file['error'] = 'Filetype not allowed'
        else:
            return True
        return False

    def get_file_size(self, file):
        file.seek(0, 2)  # Seek to the end of the file
        size = file.tell()  # Get the position of EOF
        file.seek(0)  # Reset the file position to the beginning
        return size

    def get(self):
        template_vars = {}
        self.render("upload-files.html", **template_vars)

    @tornado.web.asynchronous
    def post(self):
        print "POST files:"
        print [f['filename'] for f in self.request.files['file']]
        print "POST arguments:"
        print self.request.arguments

        results = []

        msg = "Following files were uploaded:<br>"
        for f in self.request.files['file']:
            result = {}
            result['name'] = f['filename']
            result['type'] = magic.from_file(f, mime=True)
            result['size'] = self.get_file_size(f)

            if self.validate(result):


            extension = os.path.splitext(original_f_name)[1]

            f_name = ''.join(random.choice(string.ascii_lowercase + string.digits) for x in range(6))
            final_filename = f_name + extension
            output_file = open("uploads/" + final_filename, 'w')
            output_file.write(f['body'])
            msg = msg + original_f_name + "<br>"
        results.append(result)

        #self.finish(msg)



# class FileHandler(tornado.web.RequestHandler):
#     file_body = self.request.files['filefieldname'][0]['body']
#     img = Image.open(StringIO.StringIO(file_body))
#     img.save("../img/", img.format)
__author__ = 'amodig'

import hashlib
import tornado.web


class Gravatar(tornado.web.UIModule):
    def render(self, email, size=40, image_type='jpg'):
        email_hash = hashlib.md5(email).hexdigest()
        return "http://gravatar.com/avatar/{0}?s={1}.{2}".format(email_hash, size, image_type)
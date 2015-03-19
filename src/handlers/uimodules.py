__author__ = 'amodig'

import hashlib
import tornado.web

import markdown2


class Gravatar(tornado.web.UIModule):
    def render(self, email, size=40, image_type='jpg'):
        email_hash = hashlib.md5(email).hexdigest()
        return "http://gravatar.com/avatar/{0}?s={1}.{2}".format(email_hash, size, image_type)


class Markdown(tornado.web.UIModule):
    def render(self, text):
        html = markdown2.markdown(text)
        print html
        return self.render_string("modules/bio.html", html=html)
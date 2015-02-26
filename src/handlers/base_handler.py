import tornado.auth
import tornado.escape
import tornado.gen
import tornado.httpserver

from tornado.ioloop import IOLoop
from tornado.web import asynchronous, RequestHandler, Application
from tornado.httpclient import AsyncHTTPClient

import json

class BaseHandler(RequestHandler):
    def get_login_url(self):
        return u"/login"

    def get_current_user(self):
        user_json = self.get_secure_cookie("user")
        if user_json:
            return tornado.escape.json_decode(user_json)
        else:
            return None

    def json_ok(self, data):
        info = {}
        info.update(data)
        j_ = json.dumps(info)
        self.set_header("Content-Type", "application/json")
        self.finish("%s\n" % j_)

    # Allows us to get the previous URL
    def get_referring_url(self):
        try:
            _, _, referer, _, _, _ = urlparse.urlparse(self.request.headers.get('Referer'))
            if referer:
                return referer
        # Test code will throw this if there was no 'previous' page
        except AttributeError:
            pass
        return '/'

    def get_flash(self):
        flash = self.get_secure_cookie('flash')
        self.clear_cookie('flash')
        return flash

    def get_essentials(self):
        mp = {k: ''.join(v) for k, v in self.request.arguments.iteritems()}
        print mp

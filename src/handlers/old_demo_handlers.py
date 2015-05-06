__author__ = 'amodig'

from base_handler import *
from handlers import LoginHandler
from charts_handlers import *
from process_handlers import *

from tornado import escape
from bson.objectid import ObjectId

import bcrypt
import bson.json_util
import functools
import threading
import time
import logging


"""
DEMO handlers that are (apparently by Alex Gao) originated from:
https://github.com/bootandy/tornado_sample

Might contain something useful, or not.
"""


class AnalyzerHandler(BaseHandler):
    def get(self):
        messages = self.application.syncdb.messages.find()

    def post(self):
        pass


class ThreadHandler(tornado.web.RequestHandler):
    def perform(self, callback):
        # do something cuz hey, we're in a thread!
        time.sleep(5)
        output = 'foo'
        tornado.ioloop.IOLoop.instance().add_callback(functools.partial(callback, output))

    def initialize(self):
        self.thread = None

    @tornado.web.asynchronous
    def get(self):
        self.thread = threading.Thread(target=self.perform, args=(self.on_callback,))
        self.thread.start()

        self.write('In the request')
        self.flush()

    def on_callback(self, output):
        logging.info('In on_callback()')
        self.write("Thread output: %s" % output)
        self.finish()


"""
async demo - creates a constantly loading webpage which updates from a file.
'tail -f data/to_read.txt' >> webpage
Blocks. Can't be used by more than 1 user at a time.
"""
class TailHandler(BaseHandler):
    @asynchronous
    def get(self):
        self.file = open('data/to_read.txt', 'r')
        self.pos = self.file.tell()

        def _read_file():
            # Read some amount of bytes here. You can't read until newline as it
            # would block
            line = self.file.read(40)
            last_pos = self.file.tell()
            if not line:
                self.file.close()
                self.file = open('data/to_read.txt', 'r')
                self.file.seek(last_pos)
                pass
            else:
                self.write(line)
                self.flush()

            IOLoop.instance().add_timeout(time.time() + 1, _read_file)
        _read_file()


class EmailMeHandler(BaseHandler):
    @tornado.web.asynchronous
    @tornado.gen.engine
    def get(self):
        http_client = AsyncHTTPClient()
        mail_url = self.settings["mandrill_url"] + "/messages/send.json"
        mail_data = {
            "key": self.settings["mandrill_key"],
            "message": {
                "html": "html email from tornado sample app <b>bold</b>",
                "text": "plain text email from tornado sample app",
                "subject": "from tornado sample app",
                "from_email": "hello@retechnica.com",
                "from_name": "Hello Team",
                "to": [{"email": "sample@retechnica.com"}]
            }
        }
        mail_data = {
            "key": self.settings["mandrill_key"],
        }
        mail_url = self.settings["mandrill_url"] + "/users/info.json"

        body = escape.json_encode(mail_data)
        response = yield tornado.gen.Task(http_client.fetch, mail_url, method='POST', body=body)
        logging.info(response)
        logging.info(response.body)

        if response.code == 200:
            self.set_secure_cookie('flash', "sent")
            self.redirect('/')
        else:
            self.set_secure_cookie('flash', "FAIL")
            self.redirect('/')


class MyStaticFileHandler(tornado.web.StaticFileHandler):
    def set_extra_headers(self, path):
        # Disable cache
        self.set_header('Cache-Control', 'no-store, no-cache, must-revalidate, max-age=0')


class MessageHandler(BaseHandler):
    @tornado.web.authenticated
    def get(self):
        users = self.application.syncdb['users'].find()
        self.render("message.html", user=self.get_current_user(), users=users, notification=self.get_flash())

    def post(self):
        sent_to = self.get_argument('to')
        sent_from = self.get_current_user()
        message = self.get_argument("message")
        msg = {}
        msg['from'] = sent_from
        msg['to'] = sent_to
        msg['message'] = message

        if self.save_message(msg):
            self.set_secure_cookie('flash', "Message Sent")
            self.redirect(u"/hello")
        else:
            print "error_msg"

    def save_message(self, msg):
        return self.application.syncdb['messages'].insert(msg)


class DataPusherHandler(BaseHandler):
    #@asynchronous
    def get(self):
        data = self.application.syncdb['data_pusher'].find()
        self.render("data_pusher.html", user=self.get_current_user(), data=data)

    def post(self):
        print 'POST DataPusherHandler'
        try:
            user = self.get_current_user()
            if not user:
                user = 'not logged in '
        except:
            user = 'not logged in '

        message = self.get_argument("message")
        msg = {'message': user + ' : ' + message}

        self.application.syncdb['data_pusher'].insert(msg)
        self.write('done')
        self.finish()
        return
        #self.redirect('/pusher')


class DataPusherRawHandler(BaseHandler):
    def get(self):
        def _read_data():
            m_id = self.get_argument('id', '')
            print m_id
            if m_id:
                data = list(self.application.syncdb['data_pusher'].find(
                    {'_id': {'$gt': ObjectId(m_id)}}))
            else:
                data = list(self.application.syncdb['data_pusher'].find())

            s = json.dumps(data, default=bson.json_util.default)
            self.write(s)
            self.flush()
        _read_data()


class FacebookDemoHandler(BaseHandler):
    @tornado.web.authenticated
    def get(self):
        self.render("fb_demo.html", user=self.get_current_user(), fb_app_id=self.settings['facebook_app_id'])


class WildcardPathHandler(BaseHandler):
    """An example how to handle wildcard paths"""
    def initialize(self):
        self.supported_path = ['good', 'nice']

    # prepare() called just before either GET or POST like a later version of initialize()
    def prepare(self):
        print self.request.path
        action = self.request.path.split('/')[-2]
        if action not in self.supported_path:
            self.write("<html><body>I don't like that url</body></html>")
            self.finish()
            return

    def get(self, action):
        self.write('<html><body>I am happy you went to '+action+'</body></html>')
        self.finish()

    def post(self, action):
        self.write('<html><body>I am happy you went to '+action+'</body></html>')
        self.finish()


class ReferBackHandler(BaseHandler):
    """Return to previous page."""
    def get(self):
        print 'Returning back to previous page'
        self.set_secure_cookie("flash", "returning back to previous page")
        self.redirect(self.get_referring_url())


"""""""""""
UI handlers
"""""""""""


class FormHandler(BaseHandler):
    """Handler for login forms?"""
    def get(self):
        user = self.get_current_user()
        if None == user:
            self.redirect("/login")
        messages = self.application.syncdb.messages.find()
        self.render("form.html", messages=messages, notification=self.get_flash(), user=self.get_current_user())

    def post(self):
        description = self.get_argument('description', '')
        user = self.application.syncdb['users'].find_one({'user': self.get_current_user()})
        user['description'] = description
        auth = self.application.syncdb['users'].save(user)
        self.redirect(u"/index")


class NotificationHandler(BaseHandler):
    def get(self):
        messages = self.application.syncdb.messages.find()
        self.render("notification.html", messages=messages, notification='hello')


class SlidyHandler(BaseHandler):
    def get(self):
        messages = self.application.syncdb.messages.find()
        self.render("slidy.html", messages=messages, notification=self.get_flash())


class PopupHandler(BaseHandler):
    def get(self):
        messages = self.application.syncdb.messages.find()
        self.render("popup.html", notification=self.get_flash())


class MenuTagsHandler(BaseHandler):
    def get(self):
        self.render("menu_tags.html", notification=self.get_flash())


"""""""""""
Login handlers
"""""""""""


class NoneBlockingLogin(BaseHandler):
    """
    Runs Bcrypt in a thread - Allows tornado to server up
    other handlers but can not process multiple logins simultaneously
    """
    def get(self):
        messages = self.application.syncdb.messages.find()
        self.render("login.html", notification=self.get_flash())

    def initialize(self):
        self.thread = None

    @tornado.web.asynchronous
    def post(self):
        email = self.get_argument('email', '')
        password = self.get_argument('password', '')
        user = self.application.syncdb['users'].find_one({'user': email})

        self.thread = threading.Thread(target=self.compute_password, args=(password, user,))
        self.thread.start()

    def compute_password(self, password, user):
        if user and 'password' in user:
            if bcrypt.hashpw(password, user['password']) == user['password']:
                tornado.ioloop.IOLoop.instance().add_callback(functools.partial(self._password_correct_callback, user['user']))
                return
        tornado.ioloop.IOLoop.instance().add_callback(functools.partial(self._password_fail_callback))

    def set_current_user(self, username):
        print "Set current user: " + username
        if username:
            self.set_secure_cookie("user", escape.json_encode(username))
        else:
            self.clear_cookie("user")

    def _password_correct_callback(self, email):
        self.set_current_user(email)
        self.redirect(self.get_argument('next', '/'))

    def _password_fail_callback(self):
        self.set_flash('Error Login incorrect')
        error_msg = u"?error=" + escape.url_escape("Password fail")
        self.redirect(u"/login" + error_msg)


class TwitterLoginHandler(LoginHandler, tornado.auth.TwitterMixin):
    @tornado.web.asynchronous
    def get(self):
        if self.get_argument("oauth_token", None):
            self.get_authenticated_user(self.async_callback(self._on_auth))
            return
        self.authorize_redirect()

    def _on_auth(self, user):
        if not user:
            raise tornado.web.HTTPError(500, "Twitter auth failed")
        print "Auth worked"
        #user_details = self.application.syncdb['users'].find_one( {'twitter': tw_user['username'] } )
        # Create user if user not found

        self.set_current_user(tw_user['username'])
        self.redirect(u"/index")


class FacebookLoginHandler(LoginHandler, tornado.auth.FacebookGraphMixin):
    @tornado.web.asynchronous
    def get(self):
        if self.get_argument('code', False):
            self.get_authenticated_user(
                redirect_uri=self.settings['facebook_registration_redirect_url'],
                client_id=self.application.settings['facebook_app_id'],
                client_secret=self.application.settings['facebook_secret'],
                code=self.get_argument('code'),
                callback=self.async_callback(self._on_login)
                )
            return
        self.authorize_redirect(redirect_uri=self.settings['facebook_registration_redirect_url'],
                                client_id=self.settings['facebook_app_id'],
                                extra_params={'scope': 'offline_access'})  # read_stream,

    def _on_login(self, fb_user):
        # user_details = self.application.syncdb['users'].find_one( {'facebook': fb_user['id']} )
        # Create user if user not found
        self.set_current_user(fb_user['id'])
        self.redirect(u"/index")


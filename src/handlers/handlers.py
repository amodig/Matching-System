from base_handler import *
from charts_handlers import *
from process_handlers import *
from profile_handlers import *

from tornado import escape
from bson.objectid import ObjectId
import bcrypt
import hashlib
import urllib

import logging
import bson.json_util
import time
import threading
import functools


class AnalyzerHandler(BaseHandler):
    def get(self):
        messages = self.application.syncdb.messages.find()

    def post(self):
        pass


class FormHandler(BaseHandler):
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


class LoginHandler(BaseHandler):
    @tornado.web.asynchronous
    def get(self):
        error_msg = self.get_argument("error", default="")
        self.render("login.html", next=self.get_argument("next", default=u"/control"),
                    notification=self.get_flash(),
                    message=self.get_argument("error", ""),
                    error_msg=error_msg)

    @tornado.gen.coroutine
    def post(self):
        username = self.get_argument("username", default="")
        password = self.get_argument("password", default="").encode("utf-8")
        user = yield self.application.db['users'].find_one({'user': username})  # returns a Future
        # Warning bcrypt will block IO loop:
        if user is None:
            print "User not found"
            error_msg = u"?error=" + escape.url_escape("User not found.")
            self.redirect(u"/login" + error_msg)
        elif user['password'] and bcrypt.hashpw(password, user['password'].encode("utf-8")) == user['password']:
            print "Login correct: " + username
            self.set_current_user(username)
            self.redirect(self.get_argument("next", default=u"/control"))
            print self.get_argument("next", default=u"/control")
        else:
            print "Login incorrect: " + username
            self.set_secure_cookie('flash', "Login incorrect!")
            error_msg = u"?error=" + escape.url_escape("Login incorrect.")
            self.redirect(u"/login" + error_msg)

    def set_current_user(self, username):
        print "Set current user: " + username
        if username:
            self.set_secure_cookie("user", escape.json_encode(username))
        else:
            self.clear_cookie("user")


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

    def _password_correct_callback(self, email):
        self.set_current_user(email)
        self.redirect(self.get_argument('next', '/'))

    def _password_fail_callback(self):
        self.set_flash('Error Login incorrect')
        error_msg = u"?error=" + escape.url_escape("Password fail")
        self.redirect(u"/login" + error_msg)


class RegisterHandler(LoginHandler):
    @tornado.gen.coroutine
    def _find_one(self, entry, query):
        print "Checking db: " + self.application.db.name + ", collection: " + self.application.db['users'].name
        # find_one returns None if no matching document
        doc = yield self.application.db['users'].find_one({entry: query})
        raise gen.Return(doc)  # has to raise a gen.Return in Python 2

    @tornado.web.asynchronous
    def get(self):
        self.render("register.html", next=self.get_argument("next", "/"))

    @tornado.gen.coroutine
    def post(self):
        # Validate registration
        # (add a spam trap perhaps?)

        # Collect inputs (no need to sanitize inputs with MongoDB)
        name = self.get_argument("name", "")
        email = self.get_argument("email", "")
        username = self.get_argument("username", "")
        password = self.get_argument("password", "")

        # Save to database
        # (should this ensure an initial users collection?)

        # Check unique fields
        query_email = yield self._find_one("email", email)
        query_username = yield self._find_one("user", username)

        if query_email is not None:
            print email + " already taken:"
            print query_email
            error_msg = u"?error=" + escape.url_escape("This email is already registered.")
            self.redirect(u"/register" + error_msg)
        elif query_username is not None:
            print username + " already taken"
            print query_username
            error_msg = u"?error=" + escape.url_escape("This username is already taken.")
            self.redirect(u"/register" + error_msg)
        else:
            hashed_passwd = bcrypt.hashpw(password, bcrypt.gensalt(8))  # warning bcrypt will block IO loop!
            user = {}
            user['user'] = username  # use username as the "user" field when using "users" collection
            user['email'] = email
            user['name'] = name
            user['password'] = hashed_passwd
            user['bio'] = name  # empty bio with just name
            # save user data into database
            auth = yield self.application.db['users'].save(user)
            self.set_current_user(username)
            # Add two-step verification?
            self.redirect(u"/control")


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


class LogoutHandler(BaseHandler):
    def get(self):
        self.clear_cookie("user")
        self.redirect(u"/login")


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


class IndexHandler(MainBaseHandler):
    @tornado.web.authenticated
    def get(self):		
        self.render("index.html")

    @tornado.web.authenticated
    def post(self):
        self.application.iter_num += 1
        
        key_phrase = self.get_argument('key_phrase', '').split('_')
        indexes = []
        
        for k in key_phrase:
            indexes.append(self.application.keywords.index(k))

    def __del__(self):
        super(BaseHandler, self).__del__(*args, **kwargs)
        self.application.iter_num = 0
        
"""
#        for keyword in self.keywords:
#            if self._lists_overlap(key_phrase, keyword.split()):
#                selected_keys.append(keyword)
"""


class TablesHandler(BaseHandler):
    @tornado.web.authenticated 
    def get(self):
        self.render("tables.html")


class TablesDataHandler(BaseHandler):
    @tornado.web.authenticated 
    def get(self):
        words, person_names = zip(*[(person_info["keywords"], person_info["name"]) for person_info in
                                    self.application.corpuses_name_id.values()])
        message = {
            "tables":
                [
                    {
                        "persons":person_names, 
                        "words":words
                    }
                ]
            }
        self.json_ok(message)

        
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


class FacebookDemoHandler(BaseHandler):
    @tornado.web.authenticated
    def get(self):
        self.render("fb_demo.html", user=self.get_current_user(), fb_app_id=self.settings['facebook_app_id'])


class GravatarHandler(BaseHandler):
    @staticmethod
    def get_gravatar_url(email):
        # random patterned background:
        default = 'identicon'
        size = 40
        # construct the url
        gravatar_url = "http://www.gravatar.com/avatar/" + hashlib.md5(email.lower()).hexdigest() + "?"
        gravatar_url += urllib.urlencode({'d': default, 's': str(size)})
        return gravatar_url

    def get(self):
        email = self.get_argument('email', "sample@gmail.com")
        self.render("grav.html", user=self.get_current_user(), email=email, icon=self.get_gravatar_url(email))


class WildcardPathHandler(BaseHandler):
    def initialize(self):
        self.supported_path = ['good', 'nice']

    """ prepare() called just before either get or post
    like a later version of init() """
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

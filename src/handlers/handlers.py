from base_handler import *
from charts_handlers import *
from process_handlers import *
from profile_handlers import *

import bcrypt
import hashlib
import urllib


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


class LogoutHandler(BaseHandler):
    def get(self):
        self.clear_cookie("user")
        self.redirect(u"/login")


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
        # Validate registration (add a spam trap perhaps?)

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
            yield self.application.db['users'].save(user)
            self.set_current_user(username)
            # Add two-step verification?
            self.redirect(u"/control")


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

    # def __del__(self):
    #     super(BaseHandler, self).__del__(*args, **kwargs)
    #     self.application.iter_num = 0


class TablesHandler(BaseHandler):
    @tornado.web.authenticated 
    def get(self):
        self.render("tables.html")


class TablesDataHandler(BaseHandler):
    @tornado.web.authenticated 
    def get(self):
        words, person_names = zip(*[(person_info["keywords"], person_info["name"]) for person_info in
                                    self.application.corpora_user_id.values()])
        message = {
            "tables":
                [
                    {
                        "persons": person_names,
                        "words": words
                    }
                ]
            }
        self.json_ok(message)


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

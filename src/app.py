"""Provides a Tornado seb server app for Student-Supervisor matching system.

Application includes setting Tornado handlers, configs and basic methods for the engine.
"""

from handlers.handlers import *
from handlers import uimodules

import tornado.httpserver
import tornado.gen
import tornado.web
import tornado.ioloop
import tornado.options
from tornado.options import define, options
from tornado.web import url

from copy import deepcopy
import uuid
import base64
import pickle

__author__ = "Yuan (Alex) Gao, Arttu Modig"
__credits__ = "Yuan (Alex) Gao, Arttu Modig, Kalle Ilves, Han Xiao"
__license__ = "MIT"
__version__ = "0.1"
__maintainer__ = "Arttu Modig"
__email__ = "arttu.modig@gmail.com"
__status__ = "Prototype"

# tornado config
define("port", default=8899, type=int)
define("config_file", default="app_config.yml", help="app_config file")

# MONGO_SERVER_ADDRESS = '192.168.1.68'
MONGO_SERVER_ADDRESS = 'localhost'
MONGO_SERVER_PORT = 27017


class Application(tornado.web.Application):
    def __init__(self, **overrides):
        # self.config = self._get_config()  # could be useful?

        handlers = [
            url(r'/', LoginHandler, name='/'),

            url(r'/index', IndexHandler, name='index'),
            url(r'/charts', ChartsHandler, name='charts'),
            url(r'/charts_data', ChartsDataHandler, name='charts_data'),
            url(r'/topic_model', TopicModelHandler, name='topic_model'),
            url(r'/tables', TablesHandler, name='tables'),
            url(r'/tables_data', TablesDataHandler, name='tables_data'),
            url(r'/article_matrix', ArticleMatrixHandler, name='article_matrix'),
            url(r'/related_articles', RelatedArticlesHandler, name='related_articles'),

            url(r'/control', ProfileIndexHandler, name="profile_index"),
            url(r'/download', DownloadHandler, name="download"),
            url(r'/upload', UploadHandler, name="upload"),
            url(r'/update_bio', ProfileHandler, name="update_bio"),
            url(r'/profile', ProfileHandler, name="profile"),
            url(r'/article/([a-z0-9]+)', ArticleDataHandler, name='article/([a-z0-9]+)'),
            url(r'/article/([a-z0-9]+)/edit', ArticleDataHandler, name='article/([a-z0-9]+)/edit'),

            url(r'/form', FormHandler, name='form'),
            url(r'/next', NextHandler, name='next'),
            url(r'/remove_person', RemovePersonHandler, name='remove_person'),
            url(r'/search', SearchHandler, name='search'),
            url(r'/analyzer', AnalyzerHandler, name='analyzer'),
            url(r'/email', EmailMeHandler, name='email'),
            url(r'/message', MessageHandler, name='message'),
            url(r'/grav', GravatarHandler, name='grav'),
            url(r'/menu', MenuTagsHandler, name='menu'),
            url(r'/slidy', SlidyHandler, name='slidy'),

            url(r'/notification', NotificationHandler, name='notification'),
            url(r'/fb_demo', FacebookDemoHandler, name='fb_demo'),
            url(r'/popup', PopupHandler, name='popup_demo'),
            url(r'/tail', TailHandler, name='tail_demo'),
            url(r'/pusher', DataPusherHandler, name='push_demo'),
            url(r'/pusher_raw', DataPusherRawHandler, name='push_raw_demo'),
            url(r'/matcher/([^\/]+)/', WildcardPathHandler),
            url(r'/back_to_where_you_came_from', ReferBackHandler, name='referrer'),
            url(r'/thread', ThreadHandler, name='thread_handler'),

            url(r'/login_no_block', NoneBlockingLogin, name='login_no_block'),
            url(r'/login', LoginHandler, name='login'),
            url(r'/twitter_login', TwitterLoginHandler, name='twitter_login'),
            url(r'/facebook_login', FacebookLoginHandler, name='facebook_login'),
            url(r'/register', RegisterHandler, name='register'),
            url(r'/logout', LogoutHandler, name='logout'),
        ]

        # xsrf_cookies is for XSS protection add this to all forms: {{ xsrf_form_html() }}
        settings = {
            # static file settings
            'static_path': os.path.join(os.path.dirname(__file__), 'static'),
            # template settings
            'template_path': os.path.join(os.path.dirname(__file__), 'templates'),
            'autoescape': "xhtml_escape",  # Defaults to "xhtml_escape"
            # UI modules
            "ui_modules": uimodules,
            # authentication and security
            'cookie_secret': base64.b64encode(uuid.uuid4().bytes + uuid.uuid4().bytes),
            'twitter_consumer_key': 'KEY',
            'twitter_consumer_secret': 'SECRET',
            'facebook_app_id': '180378538760459',
            'facebook_secret': '7b82b89eb6aa0d3359e2036e4d1eedf0',
            'facebook_registration_redirect_url': 'http://localhost:8888/facebook_login',
            'mandrill_key': 'KEY',
            'mandrill_url': 'https://mandrillapp.com/api/1.0/',
            'xsrf_cookies': False,  # If true, Cross-site request forgery protection will be enabled.
            # general settings
            'debug': True,
            'log_file_prefix': "tornado.log",
        }

        tornado.web.Application.__init__(self, handlers, **settings)

        # Connect to MongoDB
        self.client = motor.MotorClient(MONGO_SERVER_ADDRESS, MONGO_SERVER_PORT)
        # Choose correct database
        self.db = self.client['app']
        # self.db = self.client['test-thank']

        # following part is for Analyzer
        @tornado.gen.coroutine
        def set_keywords_parameters(source='xml'):
            print "Set keywords for analyzer..."
            print "Using source:", source
            self.keywords_number = 10

            if source is 'xml':
                self._num_of_corpora = "all"
                self.abstracts_filename = "../docs/abstracts/abstracts.xml"  # information of all abstracts
                self.extractors = Extractors(file_name=self.abstracts_filename)
                self.original_corpora, self.uploader_names, self.titles = self.extractors.get_information_from_xml(10000)
            elif source is 'db':
                self._num_of_corpora = "db"
                self.extractors = Extractors(database=self.db, collection=u'fs.files')
                info = yield self.extractors.get_information_from_database()
                self.original_corpora = info['corpora']
                self.uploader_names = info['uploader_names']
                self.titles = info['titles']

                # set keywords (might take a while):
                # yield self.extractors.set_keywords_from_database()  # recommended to run only when needed

            print "Paper uploaders:", self.uploader_names

            # information of all keywords as a set:
            self.keywords_filename = "../docs/keywords/abstract_%s.txt" % self._num_of_corpora
            # keyword lists of each abstract:
            self.corpus_keywords_filename = "../docs/keywords/corpus_abstract_%s.txt" % self._num_of_corpora
            # load and set abstract and keyword corpora
            self.corpus_keywords_file_obj = open(self.corpus_keywords_filename, 'r')
            # set preprocessed keyword corpora (this is different than original corpora)
            self.corpora = pickle.load(self.corpus_keywords_file_obj)
            self.corpus_keywords_file_obj.close()

        def form_persons_info():
            print "amount of original corpora:", len(self.original_corpora)
            print "amount of preprocessed corpora:", len(self.corpora)
            print "amount of uploaders:", len(self.uploader_names)
            # assert(len(self.original_corpora) == len(self.corpora) == len(self.uploader_names))  # for persons_info
            self.corpora_user_id = {}
            self.persons_info = []  # this variable is a list that contains all information of persons
            person_id = 0
            for title, original_corpus, decomposed_corpus, user in zip(self.titles, self.original_corpora,
                                                                       self.corpora, self.uploader_names):
                if user not in self.corpora_user_id.keys():
                    self.corpora_user_id[user] = {}
                    self.corpora_user_id[user]["id"] = person_id
                    person_id += 1
                    self.corpora_user_id[user]["name"] = user
                    self.corpora_user_id[user]["email"] = "Random@email.com"

                    self.corpora_user_id[user]["room"] = "D212"
                    self.corpora_user_id[user]["phone"] = "+358 9999 9999"
                    self.corpora_user_id[user]["homepage"] = "http://random.homepage.com"
                    self.corpora_user_id[user]["reception_time"] = "By appointment"
                    self.corpora_user_id[user]["group"] = "Secure Systems"
                    self.corpora_user_id[user]["keywords"] = []
                    self.corpora_user_id[user]["articles"] = []
                    self.corpora_user_id[user]["profile_picture"] = "http://upload.wikimedia.org/wikipedia/commons/2/22/Turkish_Van_Cat.jpg"
                    # self.corpora_user_id[user]["profile_picture"] = GravatarHandler.get_gravatar_url(email)

                self.corpora_user_id[user]["articles"].append({
                    "author_profile_picture":
                        "http://upload.wikimedia.org/wikipedia/commons/2/22/Turkish_Van_Cat.jpg",
                    "id": 1, "title": "%s" % title, "abstract": "%s" % original_corpus,
                    "url": "http://images4.fanpop.com/image/photos/14700000/Beautifull-cat-cats-14749885-1600-1200.jpg"
                })

                # append keywords in list corpora_user_id[name]["keywords"]
                for keyword in decomposed_corpus.split(','):
                    for keyword_info in self.keywords_info:
                        if keyword == keyword_info["text"]:
                            self.corpora_user_id[user]["keywords"].append(keyword_info["id"])

        def set_iteration_parameters():
            # number of iteration
            self.iter_num = 0

        def analyze_data():
            self.analyzer = Analyzer(self.keywords_list, self.corpora)

        def form_keywords_info():
            # set of all keywords
            self.keywords_file_obj = open(self.keywords_filename, 'r')
            self.keywords_set = pickle.load(self.keywords_file_obj)
            # length of all keywords
            self.current_selected_keyword_length = len(list(self.keywords_set))
            # list of all keywords information: a dictionary which contains ( "id", "text",  "exploitation",
            # "exploration" ) as keys
            self.keywords_list = list(self.keywords_set)[:self.current_selected_keyword_length]
            self.keywords_id = range(0, self.current_selected_keyword_length)
            self.form_new_keywords_information()
            self.keywords_file_obj.close()

        # set keywords parameters
        tornado.ioloop.IOLoop.instance().run_sync(lambda: set_keywords_parameters(source='xml'))  # xml or db

        set_iteration_parameters()
        form_keywords_info()
        form_persons_info()
        analyze_data()
        print "Ready!"

    def form_new_keywords_information(self):
        keywords_exploitation = [0.1] * len(self.keywords_list)
        keywords_exploration = [0.9] * len(self.keywords_list)
        self.keywords_info = zip(self.keywords_id, self.keywords_list, keywords_exploitation, keywords_exploration)
        self.keywords_keys = ("id", "text",  "exploitation", "exploration")
        self.keywords_info = [dict(zip(self.keywords_keys, keyword_info)) for keyword_info in self.keywords_info]
        self.keywords = self.keywords_list[self.keywords_number * self.iter_num: self.keywords_number *
                                                                                 (self.iter_num + 1)]
        # keywords after ranking, this variable will only be used in NextHandler
        self.ranked_keywords = deepcopy(self.keywords_info)
        # keywords after user input their preferences, this will be only be used in the SearchHandler
        self.filtered_keywords = deepcopy(self.keywords_info)
        # selected keywords, the format is the text of keyword
        self.experienced_keywords = []

    # def __del__(self):
    #    super(tornado.web.Application, self).__del__(*args, **kwargs)

# to redirect log file run python with : --log_file_prefix=mylog
def main():
    tornado.options.parse_command_line()
    http_server = tornado.httpserver.HTTPServer(Application(debug=True))
    http_server.listen(options.port)
    tornado.ioloop.IOLoop.instance().start()

if __name__ == '__main__':
    main()

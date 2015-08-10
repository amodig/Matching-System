"""Provides a Tornado seb server app for Student-Supervisor matching system.

Application includes setting Tornado handlers, configs and basic methods for the engine.
"""

from handlers.handlers import *
from handlers import uimodules
from handlers.newHandlers import *

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

__author__ = "Yuan (Alex) Gao, Arttu Modig, Kaj Sotala"
__credits__ = "Yuan (Alex) Gao, Arttu Modig, Kalle Ilves, Han Xiao, Kaj Sotala"
__license__ = "MIT"
__version__ = "0.1"
__maintainer__ = "Arttu Modig"
__email__ = "arttu.modig@gmail.com"
__status__ = "Prototype"

# Tornado config
define("port", default=8899, type=int)
define("config_file", default="app_config.yml", help="app_config file")

# MongoDB config
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
            url(r'/next', NextHandler, name='next'),
            url(r'/remove_person', RemovePersonHandler, name='remove_person'),
            url(r'/search', SearchHandler, name='search'),

            url(r'/control', ProfileIndexHandler, name="profile_index"),
            url(r'/download', DownloadHandler, name="download"),
            url(r'/upload', UploadHandler, name="upload"),
            url(r'/update_bio', ProfileHandler, name="update_bio"),
            url(r'/profile', ProfileHandler, name="profile"),
            url(r'/article/([a-z0-9]+)', ArticleDataHandler, name='article/([a-z0-9]+)'),
            url(r'/article/([a-z0-9]+)/edit', ArticleDataHandler, name='article/([a-z0-9]+)/edit'),
            url(r'/grav', GravatarHandler, name='grav'),

            url(r'/topics[/]*([0-9]*)', TopicHandler, name='topics/([0-9]*)'),
            url(r'/topic/([a-z0-9]+)/articles', TopicArticleHandler, name='topic/([a-z0-9]+)/articles'),
            url(r'/topicsearch/([\w]+)[/]*([0-9]*)', TopicSearchHandler, name='topicsearch/([a-z]+)'),
            url(r'/feedback', FeedbackHandler, name='feedback'),


            # url(r'/form', FormHandler, name='form'),
            # url(r'/analyzer', AnalyzerHandler, name='analyzer'),
            # url(r'/email', EmailMeHandler, name='email'),
            # url(r'/message', MessageHandler, name='message'),
            # url(r'/menu', MenuTagsHandler, name='menu'),
            # url(r'/slidy', SlidyHandler, name='slidy'),

            # url(r'/notification', NotificationHandler, name='notification'),
            # url(r'/fb_demo', FacebookDemoHandler, name='fb_demo'),
            # url(r'/popup', PopupHandler, name='popup_demo'),
            # url(r'/tail', TailHandler, name='tail_demo'),
            # url(r'/pusher', DataPusherHandler, name='push_demo'),
            # url(r'/pusher_raw', DataPusherRawHandler, name='push_raw_demo'),
            # url(r'/matcher/([^\/]+)/', WildcardPathHandler),
            # url(r'/back_to_where_you_came_from', ReferBackHandler, name='referrer'),
            # url(r'/thread', ThreadHandler, name='thread_handler'),

            # url(r'/login_no_block', NoneBlockingLogin, name='login_no_block'),
            # url(r'/twitter_login', TwitterLoginHandler, name='twitter_login'),
            # url(r'/facebook_login', FacebookLoginHandler, name='facebook_login'),

            url(r'/register', RegisterHandler, name='register'),
            url(r'/logout', LogoutHandler, name='logout'),
            url(r'/login', LoginHandler, name='login'),
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
        def set_keywords_parameters(metadata_source='xml', abstract_source='mallet'):
            print "Set keywords for analyzer..."
            print "Using metadata source:", metadata_source
            print "Using abstract source:", abstract_source
            self.keywords_number = 10

            if metadata_source is 'xml':
                self._num_of_corpora = "all"
                self.abstracts_filename = "../docs/abstracts/abstracts_70k.xml"  # information of all abstracts
                self.extractors = Extractors(file_name=self.abstracts_filename)
                self.original_corpora, self.uploader_names, self.titles = self.extractors.get_information_from_xml(2500)
            elif metadata_source is 'db':
                self._num_of_corpora = "db"
                self.extractors = Extractors(database=self.db, collection=u'fs.files')
                info = yield self.extractors.get_information_from_database()
                self.original_corpora = info['corpora']
                self.uploader_names = info['uploader_names']
                self.titles = info['titles']

                # set keywords (might take a while):
                # yield self.extractors.set_keywords_from_database()  # recommended to run only when needed

            if abstract_source is 'mallet':
                # information of all topics as a set:
                self.keywords_filename = "../docs/keywords/mallet_abstract.txt"
                # topic lists of each abstract:
                self.corpus_keywords_filename = "../docs/keywords/mallet_corpus_abstract.txt"
                # a dictionary of topic number-keyword list mappings
                self.topic_keywords_filename = "../docs/keywords/mallet_topic_keywords.txt"
                # a list containing dictionaries of keyword weights for each topic
                self.topic_keyword_weights_filename = "../docs/keywords/mallet_topic_keywordweights.txt"
                # a list of dicts, containing the various topicweights for each article
                self.articles_topicweights_filename = "../docs/keywords/mallet_topic_articleweights.txt"
            elif abstract_source is 'old':
                # information of all keywords as a set:
                self.keywords_filename = "../docs/keywords/abstract_%s.txt" % self._num_of_corpora
                # keyword lists of each abstract:
                self.corpus_keywords_filename = "../docs/keywords/corpus_abstract_%s.txt" % self._num_of_corpora

            # load and set abstract and keyword cd
            self.corpus_keywords_file_obj = open(self.corpus_keywords_filename, 'rb')
            # set preprocessed keyword corpora (this is different than original corpora)
            self.corpora = pickle.load(self.corpus_keywords_file_obj)
            self.corpus_keywords_file_obj.close()

            if self.topic_keywords_filename is not None:
                # set keyword data
                self.topic_keywords_obj = open(self.topic_keywords_filename, 'rb')
                self.corpus_keywords = pickle.load(self.topic_keywords_obj)
                self.topic_keywords_obj.close()

                self.topic_keyword_weights_obj = open(self.topic_keyword_weights_filename, 'rb')
                self.topic_keyword_weights = pickle.load(self.topic_keyword_weights_obj)
                self.topic_keyword_weights_obj.close()

                self.articles_topicweights_obj = open(self.articles_topicweights_filename, 'rb')
                self.articles_topicweights = pickle.load(self.articles_topicweights_obj)
                self.articles_topicweights_obj.close()

        # overlapping with old system, adding this separately to maintain compatibility with old for now...
        def form_papers_info():
            self.all_articles = [None] * len(self.corpora)
            self.articles_associated_with_topic = {}
            self.authors = {}
            i = 0

            for title, original_corpus, decomposed_corpus, user in zip(self.titles, self.original_corpora,
                                                                       self.corpora, self.uploader_names):
                self.all_articles[i] = {}
                self.all_articles[i]["title"] = title
                self.all_articles[i]["abstract"] = original_corpus
                self.all_articles[i]["people"] = []

                for author in user.split(','):
                    author = author.strip()
                    if author not in self.authors.keys():
                        self.authors[author] = {}
                        self.authors[author]["name"] = author
                        self.authors[author]["email"] = "Random@email.com"
                        self.authors[author]["room"] = "D212"
                        self.authors[author]["phone"] = "+358 9999 9999"
                        self.authors[author]["homepage"] = "http://random.homepage.com"
                        self.authors[author]["group"] = "Secure Systems"
                        self.authors[author]["profile_picture"] = "http://upload.wikimedia.org/wikipedia/commons/2/22/Turkish_Van_Cat.jpg"
                    self.all_articles[i]["people"].append(author)

                # yes this is terrible and needs a rewrite
                for keyword in decomposed_corpus.split(","):
                    for keyword_info in self.keywords_info:
                        if keyword == keyword_info["text"]:
                            def compare_article_weights(x,y):
                                x_article_dict = self.articles_topicweights[int(x)]
                                y_article_dict = self.articles_topicweights[int(y)]
                                x_weight = float(x_article_dict[keyword])
                                y_weight = float(y_article_dict[keyword])
                                comparison = 0
                                if x_weight > y_weight:
                                    comparison = -1
                                else:
                                    comparison = 1
                                return comparison

                            article_list = self.articles_associated_with_topic.get(keyword, [])
                            article_list.append(i)
                            # sort article list based on how strongly each is associated with keyword
                            sorted_article_list = sorted(article_list, cmp=compare_article_weights)
                            self.articles_associated_with_topic[keyword] = sorted_article_list



                i += 1

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
            self.keywords_file_obj = open(self.keywords_filename, 'rb')
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
        tornado.ioloop.IOLoop.instance().run_sync(lambda: set_keywords_parameters(metadata_source='xml', abstract_source='mallet'))  # xml or db, old or mallet

        set_iteration_parameters()
        form_keywords_info()
        form_persons_info()
        form_papers_info()
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

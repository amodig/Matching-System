__author__ = 'ksotala'

from base_handler import *
from random import sample
import datetime

class TopicHandler(BaseHandler):
    def _lists_overlap(self, a, b):
        return bool(set(a) & set(b))

    def get(self, key):
        # parameter 'key' defines number of keywords to return in association with each topic
        print key
        if (key is None) or (key == ''):
            key = 19
        else:
            key = int(key)
            if key > 19:
                key = 19
        self.application.form_new_keywords_information()
        self.application.analyzer.reset_current()
        # defines the number of the keywords received by the front end
        self.topics_no = 10
        self.topics = sample(self.application.keywords_set, self.topics_no)

        temp = []

        for keyword_info in self.application.keywords_info:
            if self._lists_overlap(self.topics, keyword_info["text"].split()):
                temp.append(keyword_info)

        self.application.filtered_keywords = temp
        self.application.keywords = temp

        messenger = Messenger(self.topics, self.topics, self.application, key)
        self.json_ok(messenger.generateJSONMessage())

    def post(self):
        pass

class TopicArticleHandler(BaseHandler):
    def get(self, key):

        articles = self.application.articles_associated_with_topic[key]
        articles_to_fetch = min(len(articles), 5)

        added_articles = []
        added_article_titles = set()
        i = 0
        while (len(added_articles) < articles_to_fetch):
            article = self.application.all_articles[i]
            if (article["title"]) not in added_article_titles:
                added_articles.append(articles[i])
                added_article_titles.add(article["title"])
            i += 1

        articles = added_articles

        authors = self.application.authors

        message_list = []

        for article_number in articles:
            article = self.application.all_articles[article_number]
            weight_dict = self.application.articles_topicweights[article_number]
            weight = weight_dict[key]
            message_list.append({
                "title": article["title"],
                "url": article["url"],
                "people": [authors[person] for person in article["people"]],
                "abstract": article["abstract"],
                "weight": weight
            })

        message = {"articles": message_list}

        self.json_ok(message)

    def post(self):
        pass


class TopicSearchHandler(BaseHandler):
    def _lists_overlap(self, a, b):
        return bool(set(a) & set(b))

    def get(self, searchstring, keyword_number):
        self.topics_no = 10

        if (keyword_number is None) or (keyword_number == ""):
                keyword_number = 19
        else:
            keyword_number = int(keyword_number)
            if keyword_number > 19:
                keyword_number = 19

        # reset the iteration number
        self.application.iter_num = 0
        # load the data from the front end
        keywords = searchstring.replace(" ", "_")
        # initialize temp container for sending keywords
        temp0 = []
        temp = []

        for item in self.application.corpus_keywords.items():
            item_keywords = item[1]
            if keywords in item_keywords.split(" "):
                temp0.append(item[0])

        random_topics = []
        while (len(temp0) < self.topics_no):
            topics_to_get = self.topics_no - len(temp0)
            sampled_topics = sample(self.application.keywords_set, self.topics_no)
            random_topics = list(set(sampled_topics) - set(temp0))
            temp0.extend(random_topics)

        for keyword_info in self.application.keywords_info:
            if self._lists_overlap(temp0, keyword_info["text"].split()):
                temp.append(keyword_info)

        self.application.filtered_keywords = temp
        self.application.keywords = self.application.filtered_keywords[self.application.keywords_number *
                                                                           self.application.iter_num:
                                                                           self.application.keywords_number *
                                                                           (self.application.iter_num + 1)]

        self.topics = temp0[self.application.keywords_number * self.application.iter_num:self.application.keywords_number *
                                                                           (self.application.iter_num + 1)]

        messenger = Messenger(self.topics, random_topics, self.application, keyword_number)
        self.json_ok(messenger.generateJSONMessage())

    def post(self):
        pass


class FeedbackHandler(BaseHandler):
    def get(self):
        pass

    def post(self):
        def sort_keywords(scores):
            """Sorts the keywords according to their scores. Will also filter out the keywords contained in
            the already experienced keywords.

            @params scores: scores of the keywords, the order is the same as in self.application keywords
            @return: sorted keyword pairs
            """

            # sort keywords according to their scores
            combined_pairs = zip(scores, self.application.keywords_info)
            # print self.application.experienced_keywords
            # filter out the keyword info if keyword's text is in experienced_keywords
            combined_pairs = filter(lambda x: x[1]["text"] not in self.application.experienced_keywords, combined_pairs)

            sorted_pair = zip(*sorted(combined_pairs))
            return sorted_pair[1]

        def update_keywords_info(scores):
            """Update information stored in the self.application.keywords_info

            @params Scores is a list of tuples. First element of tuple stores exploitation rate of the keyword.
                    Second element of tuple stores exploration rate of the keyword.
            """
            for i in xrange(len(self.application.keywords_info)):
                self.application.keywords_info[i]["exploitation"] = scores[i][0]
                self.application.keywords_info[i]["exploration"] = scores[i][1]

        # add experienced word, this word will not appear any in selection process
        self.application.experienced_keywords.extend([keyword["text"] for keyword in self.application.keywords])

        # load the data from the front end
        data = json.loads(self.request.body)

        # keywords info consists a list of tuples. It stores name of keyword and weight of keyword
        keywords_info = [(keyword["text"], keyword["weight"]) for keyword in data]
        # Decompose the keywords_info array to two arrays.
        # One of them contains keywords, another of them contains weights of keywords
        keywords, weights = zip(*keywords_info)
        # increase the iteration number
        self.application.iter_num += 1

        # get scores of all the keywords ordered in list order
        before = datetime.datetime.now()
        scores = self.application.analyzer.analyze(keywords, range(len(self.application.corpora)), weights, self.application.articles_topicweights)
        after = datetime.datetime.now()
        print "Time Consumption of Function Analyzer: ", after - before
        scores_sum = [sum(score) for score in scores]

        # update information if self.application.keywords_info
        update_keywords_info(scores)
        self.application.ranked_keywords = sort_keywords(scores_sum)

        # get the keywords that has highest score.
        self.application.keywords = (self.application.ranked_keywords[-self.application.keywords_number:])[::-1]

        self.topics = [keyword for keyword in self.application.keywords]
        self.topics = [topic["text"] for topic in self.topics]

        messenger = Messenger(self.topics, [], self.application, 20)
        self.json_ok(messenger.generateJSONMessage())

class Messenger():
    def __init__(self, topics, random_topics, application, number_keywords):
        self.topics = topics
        self.random_topics = random_topics
        self.keywords = application.corpus_keywords
        self.keywordweights = application.topic_keyword_weights
        self.number_keywords = number_keywords

    def generateJSONMessage(self):
        self.message_list = []
        for i in range(0, len(self.topics)):
            dictionary = self.keywordweights[int(self.topics[i])]
            keyword_list = (self.keywords[self.topics[i]]).split()
            keyword_list = keyword_list[0:self.number_keywords]
            keyword_dict_list = []
            for j in range(0, len(keyword_list)):
                weight = float(dictionary[keyword_list[j]])
                weight = round(weight, 2)
                newdict = {"label": keyword_list[j], "weight": weight}
                keyword_dict_list.append(newdict)
            dict = {"id": self.topics[i],
                  "keywords": keyword_dict_list,
                  "weight": 0.1,
                  "random": (self.topics[i] in self.random_topics),
                }
            self.message_list.append(dict)

        self.message = {"topics": self.message_list}

        return self.message

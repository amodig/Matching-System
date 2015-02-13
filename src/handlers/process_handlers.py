from base_handler import *
from random import sample
import datetime
from database_messager.mysql_messager import MysqlMessager
from numpy.linalg import norm
from numpy import apply_along_axis
from numpy import matrix


class MainBaseHandler(BaseHandler):
    def get_researcher(self, selected_words=None):
        """
        This function takes care of returning professors according to selected words by user.
        @param self pointer to class. But we don't take any variables provided by this pointer 
        @param selected_words list of words selected by user.
        @return a list of professors ranked by their score.
        """

        return ["von Etter", "Zhao", "Huizhen", "Liang"]

    def get_messages(self):
        return self.application.syncdb.messages.find()


class RemovePersonHandler(MainBaseHandler):
    def get(self):
        pass

    def post(self):
        data = json.loads(self.request.body)
        print data["id"]


class SearchHandler(MainBaseHandler):
    def _lists_overlap(self, a, b):
        return bool(set(a) & set(b))

    @tornado.web.authenticated
    def get(self):
        self.application.form_new_keywords_information()
        self.application.analyzer.reset_current()
        # defines the number of the keywords received by the front end
        self.index_keywords_no = 200
        message = {
            "keywords": sample(self.application.keywords_set, self.index_keywords_no)
        }
        self.json_ok(message)

    @tornado.web.authenticated
    def post(self):
        # reset the iteration number 
        self.application.iter_num = 0
        # load the data from the front end
        data = json.loads(self.request.body)

        # print data["keywords"]
        # decompose the search word and keywords and make them as a local keyword list
        keywords = [word for keyword in data["keywords"] for word in keyword["text"].split()]
        # print keywords
        # initialize temp container for sending keywords
        temp = []
        # iterate through each word in the list and check whether it overlaps with our local keyword list.
        for keyword_info in self.application.keywords_info:
            if self._lists_overlap(keywords, keyword_info["text"].split()):
                temp.append(keyword_info)
        self.application.filtered_keywords = temp
        self.application.keywords = self.application.filtered_keywords[self.application.keywords_number *
                                                        self.application.iter_num:self.application.keywords_number *
                                                        (self.application.iter_num + 1)]

        # sort the persons
        keywords_id = [keyword["id"] for keyword in self.application.keywords]

        def sort_persons(person):
            return len(set(person["keywords"]) & set(keywords_id))

        # persons info is a list that contains information of all persons
        persons_info = self.application.corpuses_name_id.values()
        print persons_info
        persons = sorted(persons_info, key=sort_persons, reverse=True)

        message = {
            "keywords": [
                keyword
                for keyword in self.application.keywords
            ],
            "persons": [
                person
                for person in persons
            ]

        }
        self.json_ok(message)


class NextHandler(MainBaseHandler):
    def get(self):
        pass

    def post(self):
        def sort_keywords(scores):
            """
            This function sorts the keywords according to their scores. This function also will filter out the keywords contained in the 
            @params scores: scores of h=the keywords , the order is the same as how keywords are order in self.application keywords
            @return 
            """

            # sort keywords according to their scores
            combined_pairs = zip(scores, self.application.keywords_info)
            print self.application.experienced_keywords
            # filter out the keyword info if keyword's text is in experienced_keywords
            combined_pairs = filter(lambda x: x[1]["text"] not in self.application.experienced_keywords, combined_pairs)

            sorted_pair = zip(*sorted(combined_pairs))
            return sorted_pair[1]

        def update_keywords_info(scores):
            """
            This function update information stored in the self.application.keywords_info
            @params scores is a list of tuples. First element of tuple stores exploitation rate of the keyword. Second element of tuple stores exaploration rate of the keyword
            """
            for i in xrange(len(self.application.keywords_info)):
                self.application.keywords_info[i]["exploitation"] = scores[i][0]
                self.application.keywords_info[i]["exploration"] = scores[i][1]

        # add experienced word, this word will not appear any in selection process
        self.application.experienced_keywords.extend([keyword["text"] for keyword in self.application.keywords])

        # load the data from the front end
        data = json.loads(self.request.body)

        # keywords info consists a list of tuples. It stores name of keyword and weight of keyword
        keywords_info = [(keyword["text"], keyword["weight"]) for keyword in data["keywords"]]
        # Decompose the keywords_info array to two arrays.
        # One of them contains keywords, another of them contains weights of keywords
        keywords, weights = zip(*keywords_info)
        # increase the iteration number
        self.application.iter_num = self.application.iter_num + 1

        # get scores of all the keywords ordered in list order 
        before = datetime.datetime.now()
        scores = self.application.analyzer.analyze(keywords, self.application.corpuses, weights)
        after = datetime.datetime.now()
        print "Time Consumption of Function Analyzer: ", after - before
        scores_sum = [sum(score) for score in scores]

        # update information if self.application.keywords_info
        update_keywords_info(scores)
        self.application.ranked_keywords = sort_keywords(scores_sum)

        # get the keywords that has highest score.
        self.application.keywords = (self.application.ranked_keywords[-self.application.keywords_number:])[::-1]

        # sort the persons
        keywords_id = [keyword["id"] for keyword in self.application.keywords]

        def sort_persons(person):
            return len(set(person["keywords"]) & set(keywords_id))

        persons_info = self.application.corpuses_name_id.values()
        persons = sorted(persons_info, key=sort_persons, reverse=True)
        message = {
            "keywords": [
                keyword
                for keyword in self.application.keywords
            ],
            "persons": [
                person
                for person in persons
            ]
        }
        self.json_ok(message)


class RelatedArticlesHandler(MainBaseHandler):
    """
    This class implements the related article handler. The related article handler will hand the url /related_articles
    """

    def get(self):
        pass

    def post(self):
        """
        This function receives information of paper's ID and then send back the cosine distance between this paper and
        other papers
        :return:
        """
        # load the data from the front end
        data = json.loads(self.request.body)
        paper_id = data["id"]
        feature_matrix = self.application.analyzer._X.T
        feature_vector = feature_matrix[paper_id - 1, :]

        # calculate the cosine distance between selected vector and all other vectors.
        array_of_inner_product = \
            feature_vector * \
            feature_matrix.T  # calculate the inner product between target vector and all other feature vectors
        norm_feature_vector = norm(feature_vector)  # calculate the norm of feature vector
        norm_all_vector = apply_along_axis(norm, 1, feature_matrix)
        cosine_distance = (array_of_inner_product / norm_feature_vector / norm_all_vector)
        cosine_distance = cosine_distance.tolist()[0]
        cosine_distance = matrix(sorted(cosine_distance)[:10])
        # set display parameter for front end
        display_distance = (cosine_distance - cosine_distance[cosine_distance > 0].min()) / \
                           (cosine_distance[cosine_distance > 0].max() - cosine_distance[cosine_distance > 0].min())
        print display_distance

        display_distance = display_distance.tolist()[0]

        # make messages
        sorted_index = [i[0] for i in
                        sorted(enumerate(display_distance), key=lambda x: x[1])]  # get index of element in sorted array
        # setup the connection with database
        mm = MysqlMessager(database="keyword_app")
        sql = "select AbstractID,Title,Abstract, AutherName from Abstracts where AbstractID in %s;" \
              % str(tuple(sorted_index))
        mm.excute_sql(sql)
        iterator = mm.fetch()
        message = {
            "related_articles": [{"id": data_row[0], "distance": display_distance[element], "title": data_row[1],
                                  "abstract": data_row[2],
                                  "author": data_row[3], } for data_row, element in
                                 zip(iterator, sorted_index[::-1][:10])]
        }
        print message
        self.json_ok(message)




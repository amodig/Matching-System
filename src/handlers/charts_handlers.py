from analyzer.analyzer import Analyzer
from analyzer.extractors import Extractors
from database_messager.mysql_messager import MysqlMessenger

import numpy

from base_handler import *


class ChartsHandler(BaseHandler):
    @tornado.web.authenticated        
    def get(self):		
        self.render("charts.html")


class ChartsDataHandler(BaseHandler):
    @tornado.web.authenticated        
    def get(self):		
        message = {
            "charts": [
                self.__form_person_weights_relationshp(),
                self.__form_person_keywords_counts_relationship()
            ],
            "articles":
                self.__form_article_correlation_relationship()
        }
        self.json_ok(message)
        
    def __form_person_weights_relationshp(self):
        """
        Form relationship between persons and the total weight of all the keywords
        """
        return {
                "persons": ["aaa", "aaa", "aaa", "aaa", "aaa", "aaa", "aaa"],
                "data": [15, 23, 22, 11, 15, 6, 33]
                }

    def __form_person_keywords_counts_relationship(self):
        """
        Form relationship between persons and total count of each keyword
        """
        word_counts, person_names = zip(*[(len(person_info["keywords"]), person_info["name"]) for person_info in
                                          self.application.corpuses_name_id.values()])
        return {
                "persons": person_names,
                "data": word_counts
        }

    def __form_article_correlation_relationship(self):
        self._mm = MysqlMessenger(database="keyword_app")
        sql = "select * from Abstracts;"
        self._mm.execute_sql(sql)
        iter = self._mm.fetch()
            
        #feature_matrix = self.application.analyzer._X()
        #correlation_matrix =  feature_matrix.T * feature_matrix
        
        # the third colum is title and the 
        return [{ "title": row[2].decode('latin1'), "id": row[0]} for row in iter]


class ArticleMatrixHandler(BaseHandler):
    @tornado.web.authenticated
    def post(self):
        data = json.loads(self.request.body)
        # this number decides limitation of different articles
        representatio_limit = 20
        correlation_matrix = numpy.sqrt(self.application.analyzer._X.T * self.application.analyzer._X)  
        
        self._mm = MysqlMessenger(database="keyword_app")
        sql = "select AbstractID, Title, Abstract, AuthorName from Abstracts where AbstractID in %s;" % (tuple(data["articles"]),)
        print sql
        self._mm.execute_sql(sql)
        iter = self._mm.fetch()
        # this variable shows limit for two different representations,
        # if the web site requires more articles than this number, than we use second representations
        # otherwise it returns firsts one
        limit = 10
        if len(data["articles"]) <= limit:
            message = {
                "matrix": [[{"id": data_row[0], "value": element, "title":  data_row[1], "abstract": data_row[2],
                             "author": data_row[3]}
                for data_row, element in zip(iter, matrix_row)]
                for matrix_row in correlation_matrix[data["articles"], :][:, data["articles"]].tolist()],
                # "matrix": [[{"id": 1, "value": 0.99, "title":  "title", "abstract": "abstract"},
                #             {"id": 2, "value": 0.5, "title":  "title", "abstract": "abstract"}],
                #
                #             [{"id": 1, "value": 0.99, "title":  "title", "abstract": "abstract"},
                #             {"id": 2, "value": 0.5, "title":  "title", "abstract": "abstract"}]],
                "topic_model_relation":
                {
                    "1": 1, "2": 1, "3": 1, "4": 1, "5": 1
                },
                "topic_data":
                {
                    1:
                    [
                        {"text": "Model Selection", "possibility": 0.2},
                        {"text": "Sample Size", "possibility": 0.2},
                        {"text": "Generic Model", "possibility": 0.4},
                        {"text": "Active Learning", "possibility": 0.1},
                        {"text": "Logistic Regression", "possibility": 0.1}
                    ]

                }
            }
            self.json_ok(message)
        else:
            message = {
                "matrix":
                [
                    [{"value": elem} for elem in row] for row in correlation_matrix.tolist()
                ]
            }
            self.json_ok(message)


class TopicModelHandler(BaseHandler):
    def get(self):
        return

    def post(self):
        return

"""
This class deals with way of getting information from different sources
Currently, it includes getting information from 
1. name of all researchers paper
2. 70k abstracts of paper from ArXiv
"""

from __future__ import division
from lxml import etree

import nltk
import pickle
import motor
import tornado.gen
import tornado.ioloop


class PhraseExtractor():
    def __init__(self):
        self.lemmatizer = nltk.WordNetLemmatizer()
        self.stemmer = nltk.stem.porter.PorterStemmer()

    def leaves(self, tree):
        """Finds NP (nounphrase) leaf nodes of a chunk tree."""
        for subtree in tree.subtrees(filter=lambda t: t.node == 'NP'):
            yield subtree.leaves()
     
    def normalise(self, word):
        """Normalises words to lowercase and stems and lemmatizes it."""
        word = word.lower()
        # word = self.stemmer.stem_word(word)
        # word = self.lemmatizer.lemmatize(word)
        return word
     
    def acceptable_word(self, word):
        """Checks conditions for acceptable word: length, stopword."""
        accepted = bool(2 <= len(word) <= 40
                        and word.lower() not in self.stopwords)
        return accepted

    def get_terms(self, tree):
        for leaf in self.leaves(tree):
            term = [ self.normalise(w) for w, t in leaf if self.acceptable_word(w) ]
            yield term    

    def extract(self, text):
        # Used when tokenizing words
        sentence_re = r'''(?x)      # set flag to allow verbose regexps
              ([A-Z])(\.[A-Z])+\.?  # abbreviations, e.g. U.S.A.
            | \w+(-\w+)*            # words with optional internal hyphens
            | \$?\d+(\.\d+)?%?      # currency and percentages, e.g. $12.40, 82%
            | \.\.\.                # ellipsis
            | [][.,;"'?():-_`]      # these are separate tokensconverseur
        '''

        # Taken from Su Nam Kim Paper...
        grammar = r'''
            NBAR:
                {<NN.*|JJ>*<NN.*>}  # Nouns and Adjectives, terminated with Nouns
                
            NP:
                {<NBAR>}
                {<NBAR><IN><NBAR>}  # Above, connected with in/of/etc...
        '''
        chunker = nltk.RegexpParser(grammar)
         
        toks = nltk.regexp_tokenize(text, sentence_re)
        postoks = nltk.tag.pos_tag(toks)
        tree = chunker.parse(postoks)
         
        from nltk.corpus import stopwords
        self.stopwords = stopwords.words('english')

        terms = self.get_terms(tree)
        return terms


class Extractors():
    def __init__(self, file_name=None, database=None, collection=None):
        """
        @param self a point of class
        @param line_number number of lines to be processed as batch 
        """
        self._file_name = file_name
        self._database = database
        self._collection = collection

    def get_titles(self):
        return self.titles
        
    def get_corpora(self):
        return self.project_corpora
    
    def get_author_names(self):
        return self.author_names

    @tornado.gen.coroutine
    def get_information_from_database(self, database=None, collection=None):
        if database is None:
            database = self._database
        if collection is None:
            collection = self._collection

        cursor = database[collection].find({}, {"title": 1, "abstract": 1, "user": 1})
        corpora = []
        uploaders = []
        titles =[]
        while (yield cursor.fetch_next):
            document = cursor.next_object()
            corpora.append(document['abstract'])
            uploaders.append(document['user'])
            titles.append(document['title'])
        info = {"corpora": corpora, "uploader_names": uploaders, "titles": titles}
        raise tornado.gen.Return(info)

    def get_information_from_xml(self, number_of_corpora, file_name=None):
        """
        Read papers from database and return all the words (and paper titles) that belongs to one author in a list
        :param number_of_corpora: word limit
        :param file_name: file name
        :return corpora: list of all word corpus
        :return uploader_names: list of all authors
        :return titles: list of all titles
        """
        corpora = []
        author_names = []
        titles = []
        if file_name is None:
            file_name = self._file_name
            tree = etree.parse(file_name)  # etree parses XML files
            root = tree.getroot()
        for article in root.iterchildren():
            for element in article.iterchildren():
                # if tag of element is "abstract", store the information into corpora
                if element.tag == "abstract":
                    abstract = element.text
                    corpora.append(abstract)
                if element.tag == "name":
                    author_name = element.text
                    author_names.append(author_name)
                if element.tag == "title":
                    title = element.text
                    titles.append(title)
            if len(corpora) == number_of_corpora:
                break
        return corpora, author_names, titles

    @tornado.gen.coroutine
    def set_keywords_from_database(self, database=None, collection=None):
        if database is None:
            database = self._database
        if collection is None:
            collection = self._collection

        keyword_set = set()
        corpora_representation_list = []
        phrase_extractor = PhraseExtractor()
        cursor = database[collection].find({}, {"title": 1, "abstract": 1, "user": 1})
        while (yield cursor.fetch_next):
            doc = cursor.next_object()
            print 'Extracting keywords from "' + doc['title'] + '"...'
            keywords = list(phrase_extractor.extract(doc['abstract']))
            keywords = [''.join(sublist) for sublist in keywords]
            corpora_representation_list.append(','.join(keywords))
            keyword_set |= set(keywords)  # union
        # store in application database
        # yield self.application.db['keywords'].save({"keyword_set": keyword_set, "_id": 0})
        # yield self.application.db['corpus_keywords'].save({"corpora_representation_list": corpora_representation_list,
        #                                                   "_id": 0})

        # store in pickle format
        print "Store keywords in pickle"
        file_corpus = open("../docs/keywords/corpus_abstract_db.txt", 'w')
        file_keywords = open("../docs/keywords/abstract_db.txt", 'w')
        pickle.dump(corpora_representation_list, file_corpus)
        pickle.dump(keyword_set, file_keywords)
        file_corpus.close()
        file_keywords.close()

    def set_keywords_from_abstract_xml(self, number_of_corpora, file_name=None):
        """Read a paper from a file, extract abstract and abstract corpora, and write them to text files.
        :param number_of_corpora: number of paper corpora
        :param file_name: paper file name
        """
        # if the file name exists then use a xml parser to parse the file
        if file_name is None:
            file_name = self._file_name
            tree = etree.parse(file_name)
            root = tree.getroot()
          
        # set name of file that contains keyword and name of file that contains keyword list for each abstract
        self._keywords_filename = "../../../../docs/keywords/abstract_%s.txt" % number_of_corpora
        self._corpus_keyword_filename = "../../../../docs/keywords/corpus_abstract_%s.txt" % number_of_corpora
        
        # if the file does not exist
        keyword_set = set()
        corpora_representation_list = []
        f_obj = open(self._keywords_filename, 'w')
        f_corpus_obj = open(self._corpus_keyword_filename, 'w')
        phrase_extractor = PhraseExtractor()
        for article in root.iterchildren():
            for element in article.iterchildren():
                if element.tag == "abstract":
                    abstract = element.text

                    keywords = list(phrase_extractor.extract(abstract))
                    keywords = [' '.join(sublist) for sublist in keywords]
                    corpora_representation_list.append(','.join(keywords))

                    keyword_set |= set(keywords) 
                if element.tag == "number":
                    if element.text == number_of_corpora:
                        break
        pickle.dump(corpora_representation_list, f_corpus_obj)
        pickle.dump(keyword_set, f_obj)
        f_obj.close()                  
        f_corpus_obj.close()


@tornado.gen.coroutine
def main():
    # Connect to MongoDB
    MONGO_SERVER_ADDRESS = 'localhost'
    MONGO_SERVER_PORT = 27017
    client = motor.MotorClient(MONGO_SERVER_ADDRESS, MONGO_SERVER_PORT)
    # Choose correct database
    db = client['app']
    extractor = Extractors(database=db, collection=u'fs.files')
    info = yield extractor.get_information_from_database()
    print info

if __name__ == '__main__':
    print "Run as script"
    # extractor = Extractors("../../../../docs/abstracts/abstracts.xml")
    # extractor.set_keywords_from_abstract_xml("all")

    tornado.ioloop.IOLoop.instance().run_sync(main)
    print "EOF"

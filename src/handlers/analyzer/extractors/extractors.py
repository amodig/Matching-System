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
            corpora.append(document.get('abstract', "[empty]"))
            uploaders.append(document['user'])  # should always be there!
            titles.append(document.get('title', "[No Title]"))
        info = {"corpora": corpora, "uploader_names": uploaders, "titles": titles}
        raise tornado.gen.Return(info)

    def get_information_from_bibtex(self, number_of_corpora, file_name=None):
        def processLine(splitline, thefile):
            lines = []
            openparentheses = splitline[1].count('{') - splitline[1].count('}')
            splitline[1] = splitline[1].lstrip()
            lines.append(splitline[1])
            while openparentheses > 0:
                currentline = thefile.readline()
                openparentheses = openparentheses + currentline.count('{') - currentline.count('}')
                lines.append(currentline.lstrip())
            line = " ".join(lines)
            line = line.translate(None, "{}")
            line = line[:-2]
            line = line.replace('\n', "")
            return line

        corpora = []
        author_names = []
        titles = []
        urls = []
        if file_name is None:
            file_name = self._file_name
        thefile = open(file_name, 'r')
        nextline = thefile.readline()
        while nextline:
            if "@proceedings" in nextline or "@book" in nextline:
                proceedings = True
                oktoadd = False
            elif nextline.find("@") == 0:
                proceedings = False
                current_author = None
                oktoadd = False
                url = None
            splitline = nextline.split('=')
            if (splitline[0] == '  author    ' and proceedings == False):
                current_author = processLine(splitline, thefile)
            if (splitline[0] == '  title     ' and proceedings == False):
                title = processLine(splitline, thefile)
                titles.append(title)
                corpora.append("")
                oktoadd = True
                if current_author is None:
                    print "Title " + title + " has no associated author!"
                else:
                    author_names.append(current_author)
            if (splitline[0] == '  url       ' and oktoadd):
                url = processLine(splitline, thefile)
                urls.append(url)
            if (splitline[0] == '  biburl    ' and oktoadd and url == None):
                biburl = processLine(splitline, thefile)
                urls.append(biburl)
            if len(corpora) == number_of_corpora:
                break
            nextline = thefile.readline()
        thefile.close()
        if not (len(corpora) == len(author_names) == len(titles)):
            print "Warning: mismatch in number of abstracts, authors, and titles (" + str(len(corpora)) + ", " + str(len(author_names)) + ", " + str(len(titles)) + ")"
        return corpora, author_names, titles, urls

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

    def set_keywords_from_mallet(self):
        """Read keywords and paper abstracts from Mallet topic model outputs"""
        topic_keys_filename = "../docs/mallet/mallet_topic_keys.txt"
        doc_topics_filename = "../docs/mallet/mallet_doc_topics.txt"

        output_topic_keys_filename = "../docs/keywords/mallet_abstract.txt"
        output_doc_topics_filename = "../docs/keywords/mallet_corpus_abstract.txt"

        file = open(topic_keys_filename, 'r')
        topics = dict()
        nextline = file.readline()
        while (nextline != ''):
            topic_key = nextline.split('\t')
            keyword = topic_key[2]
            keyword_with_newline_removed = keyword[:-2]
            topics[topic_key[0]] = keyword_with_newline_removed
            nextline = file.readline()
        file.close()

        topicset = set(topics.values())
        file_keyword_list = open(output_topic_keys_filename, 'w')
        pickle.dump(topicset, file_keyword_list)
        file_keyword_list.close()
        
        file = open(doc_topics_filename, 'r')
        nextline = file.readline()
        nextline = file.readline()
        corpora_representation_list = []
        while (nextline != ''):
            linelist = nextline.split('\t')
            filename = linelist[1]
            topic_list = []
            topic_number_reference = 2
            topic_probability_reference = 3
            while(float(linelist[topic_probability_reference]) >= 0.1):
                topic_name = topics[linelist[topic_number_reference]]
                topic_list.append(topic_name)
                topic_number_reference += 2
                topic_probability_reference += 2
            corpora_representation_list.append(','.join(topic_list))
            nextline = file.readline()
        file.close()
        
        file_abstract_list = open(output_doc_topics_filename, 'w')
        pickle.dump(corpora_representation_list, file_abstract_list)
        file.close()


@tornado.gen.coroutine
def main1():
    # Connect to MongoDB
    MONGO_SERVER_ADDRESS = 'localhost'
    MONGO_SERVER_PORT = 27017
    client = motor.MotorClient(MONGO_SERVER_ADDRESS, MONGO_SERVER_PORT)
    # Choose correct database
    db = client['app']
    extractor = Extractors(database=db, collection=u'fs.files')
    info = yield extractor.get_information_from_database()
    print info

@tornado.gen.coroutine
def main2():
    import sys
    sys.path.insert(0, '/Users/amodig/tornado-test/Keyword-APP/src/handlers')
    from profile_handlers import ArticleDataHandler

    # Connect to MongoDB
    MONGO_SERVER_ADDRESS = 'localhost'
    MONGO_SERVER_PORT = 27017
    client = motor.MotorClient(MONGO_SERVER_ADDRESS, MONGO_SERVER_PORT)
    # Choose correct database
    db = client['app']
    fs = motor.MotorGridFS(db, collection=u'fs')
    cursor = fs.find({}, timeout=False)
    while (yield cursor.fetch_next):
        grid_out = cursor.next_object()
        content = yield grid_out.read()
        content_type = grid_out.content_type
        title = grid_out.title
        filename = grid_out.filename
        key = grid_out._id
        abstract = ArticleDataHandler.extract_abstract(content, content_type)
        print "--------------------------------------"
        print "Title:"
        print title
        print "Filename:"
        print filename
        print "Key:"
        print key
        print "--------------------------------------"
        print "Abstract:"
        print abstract
    print "finished"


if __name__ == '__main__':
    print "Run as script"
    # extractor = Extractors("../../../../docs/abstracts/abstracts.xml")
    # extractor.set_keywords_from_abstract_xml("all")
    tornado.ioloop.IOLoop.instance().run_sync(main2)

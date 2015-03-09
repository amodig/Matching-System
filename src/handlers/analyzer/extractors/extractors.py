"""
This class deals with way of getting information from different sources
Currently, it includes getting information from 
1. name of all researchers paper
2. 70k abstracts of paper from arxiv
"""

from __future__ import division
from lxml import etree

import functools
import operator
import nltk
import string
import pickle

def isPunct(word):
  return len(word) == 1 and word in string.punctuation

def isNumeric(word):
  try:
    float(word) if '.' in word else int(word)
    return True
  except ValueError:
    return False
    
def listify(f):
    @functools.wraps(f)
    def listify_helper(*args, **kwargs):
        return list(f(*args, **kwargs))
    return listify_helper

class PhraseExtractor():
    def __init__(self):
        self.lemmatizer = nltk.WordNetLemmatizer()
        self.stemmer = nltk.stem.porter.PorterStemmer()
    def leaves(self, tree):
        """Finds NP (nounphrase) leaf nodes of a chunk tree."""
        for subtree in tree.subtrees(filter = lambda t: t.node=='NP'):
            yield subtree.leaves()
     
    def normalise(self,word):
        """Normalises words to lowercase and stems and lemmatizes it."""
        word = word.lower()
        #word = self.stemmer.stem_word(word)
        #word = self.lemmatizer.lemmatize(word)
        return word
     
    def acceptable_word(self,word):
        """Checks conditions for acceptable word: length, stopword."""
        accepted = bool(2 <= len(word) <= 40
            and word.lower() not in self.stopwords)
        return accepted
     
     
    def get_terms(self,tree):
        for leaf in self.leaves(tree):
            term = [ self.normalise(w) for w,t in leaf if self.acceptable_word(w) ]
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

        #Taken from Su Nam Kim Paper...
        grammar = r"""
            NBAR:
                {<NN.*|JJ>*<NN.*>}  # Nouns and Adjectives, terminated with Nouns
                
            NP:
                {<NBAR>}
                {<NBAR><IN><NBAR>}  # Above, connected with in/of/etc...
        """
        chunker = nltk.RegexpParser(grammar)
         
        toks = nltk.regexp_tokenize(text, sentence_re)
        postoks = nltk.tag.pos_tag(toks)
        tree = chunker.parse(postoks)
         
        from nltk.corpus import stopwords
        self.stopwords = stopwords.words('english')
         
        terms = self.get_terms(tree)
        return terms

class Extractors():

    def __init__(self,file_name):
        """
        @param self a point of class
        @param line_number number of lines to be processed as batch 
        """
        self._file_name = file_name
        # This variable stores the information of the corpuses needed in this project_corpus
        self.project_corpuses,  self.author_names,  self.titles = self.get_information(10000)
    def get_titles(self):
        return self.titles
        
    def get_corpuses(self):
        return self.project_corpuses
    
    def get_author_names(self):
        return self.author_names
    # def get_information_from_database(self):
    #     corpora = []
    #     author_names = []
    #     titles =[]
    #     sql =
    #     pass
    def get_information(self, number_of_corpus, file_name = None):
        """
        This funciton reads name of paper from database. and return all the words that belongs to one auther in a list
        @param self: Pointer to class
        @return a term frequency matrix
        """

        corpuses = []
        author_names = []
        titles = []
        keyword_set = set()
        if file_name is None:
          file_name = self._file_name
          tree = etree.parse(file_name)
          root = tree.getroot()

        for article in root.iterchildren():
            for element in article.iterchildren():
                # if tag of element is "abstract", store the information into corpuses
                if element.tag == "abstract":
                    abstract = element.text
                    corpuses.append(abstract)
                if element.tag == "name":
                    author_name = element.text
                    author_names.append(author_name)
                if element.tag == "title":
                    title = element.text
                    titles.append(title)
            if (len(corpuses)  == number_of_corpus):
                break

        return corpuses,  author_names,  titles

            
    def get_keywords_from_abstract(self, number_of_corpuses, file_name = None):
        """
        This funciton reads name of paper from database. and return all the words that belongs to one auther in a list
        @param self: Pointer to classtfm
        @return a term frequency matrix
        """
        # if the file name exits then use a xml parser to parse the file
        if file_name is None:
          file_name = self._file_name
          tree = etree.parse(file_name)
          root = tree.getroot()
          
        # set name of file that contains keyword and name of file that contains keyword list for each abstract
        self._keywords_filename = "../../../../docs/keywords/abstract_%s.txt"%number_of_corpuses
        self._corpus_keyword_filename = "../../../../docs/keywords/corpus_abstract_%s.txt"%number_of_corpuses
        
        # if the file does not exist
        keyword_set = set()
        corpuses_representation_list = []
        f_obj = open(self._keywords_filename,'w')
        f_corpus_obj = open(self._corpus_keyword_filename,'w')
        phase_extractor = PhraseExtractor()
        for article in root.iterchildren():
            for element in article.iterchildren():
                if element.tag == "abstract":
                    abstract = element.text

                    keywords = list(phase_extractor.extract(abstract))
                    keywords = [' '.join(sublist) for sublist in keywords]
                    corpuses_representation_list.append(','.join(keywords))

                    keyword_set |= set(keywords) 
                if element.tag == "number":
                    if element.text == number_of_corpuses:
                        break
        pickle.dump(corpuses_representation_list, f_corpus_obj)
        pickle.dump(keyword_set,f_obj) 
        f_obj.close()                  
        f_corpus_obj.close()
 
if __name__ == "__main__":
    extractor = Extractors("../../../../docs/abstracts/abstracts.xml")
    extractor.get_keywords_from_abstract("all")
    
        

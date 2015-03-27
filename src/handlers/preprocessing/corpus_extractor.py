"""
This class deals with way of getting information from different sources
Currently, it includes getting information from 
1. name of all researchers paper
2. 70k abstracts of paper from arXiv
"""

from __future__ import division
from lxml import etree
from os import path

from ..database_messager.mysql_messager import MysqlMessenger
from ..analyzer.extractors.extractors import PhraseExtractor

import pickle


class KeywordExtractor():
    def __init__(self, file_name=None):
        """
        @param self a point of class
        @param line_number number of lines to be processed as batch 
        """
        if file_name is None:
            self._file_name = "/home/fs/yuangao/Desktop/matching_system/src_html/handlers/articles_70k.xml"
        else:
            self._file_name = file_name
        self._mm = MysqlMessenger()
        
    def get_corpus(self, number_of_corpus, file_name=None):
        """
        This function reads name of paper from database. and return all the words that belongs to one author in a list
        @param self: Pointer to class
        @return a term frequency matrix
        """
        corpus = []
        keyword_set = set()
        if file_name is None:
            file_name = self._file_name
            tree = etree.parse(file_name)
            root = tree.getroot()

        for article in root.iterchildren():
            for element in article.iterchildren():
                if element.tag == "abstract":
                    abstract = element.text
                    corpus.append(abstract)
            if len(corpus) == number_of_corpus:
                break
        return corpus
            
    def get_from_abstract(self, number_of_corpora, file_name=None):
        """
        This function reads name of paper from database. and return all the words that belongs to one author in a list
        @param self: Pointer to class
        @return a term frequency matrix
        """
        # if the file name exits then use a xml parser to parse the file
        if file_name is None:
            file_name = self._file_name
            tree = etree.parse(file_name)
            root = tree.getroot()
          
        # set name of file that contains keyword and name of file that contains keyword list for each abstract
        self._keywords_filename = "abstract_%s.txt" % number_of_corpora
        self._corpus_keyword_filename = "corpus_abstract_%s.txt" % number_of_corpora
        
        # if the file does not exist
        if not path.isfile(self._keywords_filename):
            keyword_set = set()
            corpora_representation_list = []
            f_obj = open(self._keywords_filename, 'w')
            f_corpus_obj = open(self._corpus_keyword_filename, 'w')
            i = 0
            phase_extractor = PhraseExtractor()
            for article in root.iterchildren():
                for element in article.iterchildren():
                    if element.tag == "abstract":
                        abstract = element.text

                        keywords = list(phase_extractor.extract(abstract))
                        keywords = [' '.join(sublist) for sublist in keywords]
                        corpora_representation_list.append(','.join(keywords))

                        keyword_set |= set(keywords) 
                        i += 1
                if i == number_of_corpora:
                    break
            pickle.dump(corpora_representation_list, f_corpus_obj)
            pickle.dump(keyword_set, f_obj)
            f_obj.close()                  
            f_corpus_obj.close()
 
if __name__ == "__main__":
    keyword_extractor = KeywordExtractor("abstracts.xml", 4)
    keyword_extractor.get_from_arxiv_num(109)

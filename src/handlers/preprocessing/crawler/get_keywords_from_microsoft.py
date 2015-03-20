"""
This file downloads information through microsoft academic research API.
As the keywords list is not representive,  we need to use keywords from Microsoft
The main source is from microsoft keyword database for JMLR contained in this page:
http://academic.research.microsoft.com/Detail?entitytype=4&searchtype=9&id=126&start=1&end=10
"""
from database_messager.mysql_messager import MysqlMessager
from crawler import AbstractCrawler
import codecs


class MicrosoftKeywordsCrawler(AbstractCrawler):
    def __init__(self):
        """ Set up mysql messager
        @param self Pointer to class
        """
        super(MicrosoftKeywordsCrawler, self).__init__()
        self._mm = MysqlMessager("MSMLKeywords", database="keyword_app")

    def __repr__(self):
        """ Show descriptions of this class
        @param self Pointer to class
        """
        return "<NameCrawler name:%s>"%self.name

    def _clear_table(self):
        self._mm.clear_table()

    def _parse_and_store(self, soup):
        """ Parses the web page provided to crawl and store them in database
        @param self Pointer to class
        @param soup Structured data to be parsed
        """
        super(MicrosoftKeywordsCrawler, self)._parse_and_store(soup)
        log_file = codecs.open(self.log_dir + "name_crawler_log_file.txt",  "w", "utf-8")

        # the record shows there is about 1906 keywords in database.
        for item_div in soup.findAll("div", {"class": "conference-item" }):
            keyword = item_div.div.h3.a.contents[0]
            sql = u"INSERT INTO MSMLKeywords VALUES (default, \"%s\")" % keyword
            self._mm.excute_sql(sql, log_file)
        log_file.close()

    def _downloader(self, _url, out_folder="doc/"):
        """ Download the web page and store it python data structure
        @param self Pointer to class
        @param url URL to be downloaded
        @param out_folder Folder that stores information
        """""

        return super(MicrosoftKeywordsCrawler, self)._downloader(_url)

    def crawl(self, _url):
        """ crawl information from page
        @param self Pointer to class
        @param _url URL to be downloaded
        """
        self._clear_table()
        total_keywords_number = 1906
        for x in xrange(1, total_keywords_number + 100, 100):
            url_temp = _url + "start=%d&end=%d" % (x, x + 99)
            print url_temp
            soup = self._downloader(url_temp)
            self._parse_and_store(soup)


if __name__ == "__main__":
    keywords_crawler = MicrosoftKeywordsCrawler()
    url = "http://academic.research.microsoft.com/Detail?entitytype=4&searchtype=9&id=126&"
    keywords_crawler.crawl(url)
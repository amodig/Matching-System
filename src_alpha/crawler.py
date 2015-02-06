from urllib2 import urlopen




class AbstractCrawler(object):
    """
    Class :  AbstractCrawler
    Description: The AbstractCrawler class makes interfaces other crawlers.
    """
    def __init__(self):
        self.name = self.__class__.__name__
        self.log_dir = "crawler_logs/"

    def set_name(self, name):
        """ Set name of crawler
        @param name The name to set
        """
        self.name = name

    def __repr__(self):
        """ Show descriptions of this class
        @param self Pointer to class
        """
        return "<AbstractCrawler name:%s>"%self.name

    def _downloader(self, url, out_folder="doc/"):
        """ Download the webpage and store it python data sttructure
        @param self Pointer to class
        @param url URL to be downloaded
        @param out_folder Folder that stores information
        """""
        soup = bs(urlopen(url))
        return soup

    def _parse_and_store(self, soup):
        """ Parses the webpage privided to crawl and store them in database
        @param self Pointer to class
        @param soup Structured data to be parsed
        """
        pass

    def crawl(self):
        """ crawl informations from page
        @param self Pointer to class
        @param url URL to be downloaded
        """
        pass



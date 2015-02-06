from bs4 import BeautifulSoup as bs
from crawler import AbstractCrawler
from codecs import open as copen
from database_messager.mysql_messager import MysqlMessager
from selenium.webdriver import Firefox  # pip install selenium
from contextlib import closing
from urllib2 import Request
from urllib2 import urlopen


class NameCrawler(AbstractCrawler):
    """
    In the alpha version, we need to crawl the information of professors, postdoc researchers and lecturers.
    The information we need to store in the database is as:
    create table Persons
    (
    PersonID int not null,
    Name varchar(255),
    Email varchar(255),
    Room varchar(255),
    PhoneNumber varchar(255),
    HomePage varchar(255),
    GroupName varchar(255),
    PRIMARY KEY (PersonID)
    );
    """

    def __init__(self):
        """ Set up mysql messager
        @param self Pointer to class
        """
        super(NameCrawler, self).__init__()
        self.mm = MysqlMessager("Persons")

    def __repr__(self):
        """ Show descriptions of this class
        @param self Pointer to class
        """
        return "<NameCrawler name:%s>" % self.name

    def _parse_and_store(self, soup):
        """ Parses the webpage privided to crawl and store them in database
        @param self Pointer to class
        @param soup Structured data to be parsed
        """
        super(NameCrawler, self)._parse_and_store(soup)
        log_file = copen(self.log_dir + "name_crawler_log_file.txt", "w", "utf-8")
        self.mm.clear_table()
        for link in soup.findAll('table', {'class': ["views-table", "cols-4", "filtertable"]}):
            table = link.tbody
            for tr in table.findAll("tr"):
                tds = tr.findAll("td")
                herf = tds[0].a["href"].strip()
                name = tds[0].a.contents[0].strip()
                title = tds[1].contents[0].strip()
                room = tds[2].contents[0].strip()
                phone_num = tds[3].contents[0].strip()
                print herf, name, title, room, phone_num
                title_lower = title.lower()

                if "professor" in title_lower or \
                                "lecturer" in title_lower or \
                                "postdoc" in title_lower:
                    # homepage_soup = self._downloader(herf)
                    #print homepage_soup.findAll
                    print name
                    sql = u"INSERT INTO Persons (PersonID, Name, Title, Email, Room, PhoneNumber, HomePage, GroupName) Values (default, \"" \
                          + name + u"\",\"" \
                          + title + u"\",\"" \
                          + u" " + u"\",\"" \
                          + room + u"\",\"" \
                          + phone_num + u"\",\"" \
                          + herf + u"\",\"" \
                          + u" " + u"\")"
                    print sql
                    self.mm.excute_sql(sql, log_file)
        log_file.close()

    def _downloader(self, url, with_browser=False, out_folder="doc/"):
        """ Download the webpage and store it python daabstractta sttructure
        @param self Pointer to class
        @param url URL to be downloaded
        @param out_folder Folder that stores information
        """""
        if with_browser:
            with closing(Firefox()) as browser:
                browser.get(url)
                page_source = browser.page_source
            soup = bs(page_source)
            return soup
        else:
            """ Download the webpage and store it python data sttructure
            @param self Pointer to class
            @param url URL to be downloaded
            @param out_folder Folder that stores information
            """""
            hdr = {'User-Agent': 'Mozilla/5.0'}
            req = Request(url, headers=hdr)
            page = urlopen(req)
            soup = bs(page)
            return soup

    def crawl(self, url):
        """ crawl information from page
        @param self Pointer to class
        @param url URL to be downloaded
        """
        soup = self._downloader(url)
        self._parse_and_store(soup)


if __name__ == "__main__":
    crawler = NameCrawler()
    crawler.crawl("http://www.cs.helsinki.fi/en/people")
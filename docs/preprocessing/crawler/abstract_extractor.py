from mysql_messager import MysqlMessager
from sys import stderr
from bs4 import BeautifulSoup as BSoup
from urllib2 import Request
from urllib2 import urlopen

from contextlib import closing
from selenium.webdriver import Firefox # pip install selenium
from selenium.webdriver.support.ui import WebDriverWait

from subprocess import Popen
from subprocess import PIPE

from random import randint
from time import sleep

from sys import argv

from re import sub

from bleach import clean

from os import devnull
import unittest


class WebsiteExtractor():
    """
    Class: WebsiteExtractor
    Description: This class deals with extracting abstract from different website.
    It reads all information of whole web pages and then process the website to find the area of
    abstract.
    """
    def website_extractor(self, web_site, link):
        """
        This function is responsible for dealing with extracting abstract from different website
        """
        return self._select_website_type(web_site,link)

    def _select_website_type(self, web_site, link):
        return {
            'dl.acm.org': self._dl_acm_dealer,
            'www.researchgate.net': self._reserchgate_dealer,
            'citeseerx.ist.psu.edu': self._citeseerx_dealer,
            'journals.cambridge.org': self._journals_cambrige_dealer,
            'link.springer.com': self._link_springer_dealer,
            'ieeexplore.ieee.org': self._ieeexplore_ieee_dealer,
            'arxiv.org': self._arxiv_dealer,
            'library.wur.nl': self._library_wur_dealer,
            'eprints.pascal-network.org': self._eprints_pascal_networking_dealer,
            'papers.ssrn.com': self._paper_ssrn_dealer,
            'www.biomedcentral.com': self._biomedcentral_dealer,
            'www.igi-global.com': self._igi_global_dealer,
            'www.sciencedirect.com/': self._science_direct_dealer,
            "epubs.siam.org": self._epubs_sism_dealer,
            "helda.helsinki.fi": self._helda_helsinki_dealer,
            "projecteuclid.org": self._project_euclide_dealer,
            "www.nature.com": self._nature_dealer,
            "www.degruyter.com": self._degruyter_dealer,
            "onlinelibrary.wiley.com": self._online_library_wiley_dealer,
            "www.sciencedirect.com": self._science_direct_dealer,
        }[web_site](link)

    def _downloader(self, url, out_folder="doc/"):
        """Download the web page and store it python abstract structure

        @param self Pointer to class
        @param url URL to be downloaded
        @param out_folder Folder that stores information
        """
        with closing(Firefox()) as browser:
            browser.get(url)
            page_source = browser.page_source
        soup = BSoup(page_source)
        return soup

    def _science_direct_dealer(self, link):
        """This functions extracts abstract information from science direct web site.
        The position of the abstract is identified by following:

        soup.find("h2", text="Abstract").find_next_sibling("p")

        :param link:
        :return: abstract in the format of string
        """
        soup = self._downloader(link)
        abstract_section = soup.find("h2", text="Abstract").find_next_sibling("p")
        return abstract_section.text

    def _pnas_dealer(self, link):
        """This function extracts abstract information from web site pnas
        The position of the abstract is identified by following:
        :param link:
        :return: abstract in the format of string
        """
        raise NotImplementedError

    def _epubs_sism_dealer(self, link):
        """
        This function extracts abstract information from web site epubs sism
        The position of the abstract is identified by following:

        soup.find("div", {"class": "abstractSection"}).p

        :param link:
        :return: abstract in the format of string
        """
        soup = self._downloader(link)
        abstract_section = soup.find("div", {"class": "abstractSection"}).p
        return abstract_section.text

    def _helda_helsinki_dealer(self, link):
        """
        This function extracts abstract information from web site epubs sism
        The position of the abstract is identified by following:

        soup.find("td", {"class": "abstract-field"})

        :param link:
        :return: abstract in the foramt of string
        """
        soup = self._downloader(link)
        abstract_section = soup.find("td", {"class": "abstract-field"})
        return abstract_section.text

    def _project_euclide_dealer(self, link):
        """
        This function extracts abstract information from web site projecteuclide.org
        The position of the abstract is identified by following:

        soup.find("td", {"class": "abstract-field"})

        :param link: url link
        :return: abstract in the format of string
        """
        soup = self._downloader(link)
        abstract_section = soup.find("div", {"class": "abstract-text"})
        return abstract_section.text

    def _nature_dealer(self, link):
        """
        This function extracts abstract information from web site nature.com
        The position of the abstract is identified by following:

        soup.find("div", {"class": "first-paragraph-abs"}).p

        :param link: url link
        :return: abstract in the format of string
        """
        soup = self._downloader(link)
        abstract_section = soup.find("div", {"class": "first-paragraph-abs"}).p
        return abstract_section.text

    def _degruyter_dealer(self, link):
        """
        This function extracts abstract information from web site degruyter.com
        The position of the abstract is identified by following:

        soup.find("h2", {"class": "abstractTitle"})

        :param link: url link
        :return: abstract in the format of string
        """
        soup = self._downloader(link)
        abstract_section = soup.find("h2", {"class": "abstractTitle"}).find_next_sibling("p")
        return abstract_section.text

    def _online_library_wiley_dealer(self, link):
        soup = self._downloader(link)
        abstract_section = soup.find("div", {"class": "para"}).p
        return abstract_section.text

    def _dl_acm_dealer(self, link):
        """
        analyze abstract from dl.acm.com
        @param link: link of the paper
        @return Return abstract represented by string if parse succsed otherwise return None
        """
        soup = self._downloader(link)
        target_section = soup.find("div", {"id": "abstract"})
        if None == target_section:
            print soup
            stderr.write("download failed in function " + "_dl_acm_dealer" + "\n")
            return None
        else:
            return target_section.div.p.contents[0]

    def _reserchgate_dealer(self,website, link):
        raise NotImplementedError

    def _citeseerx_dealer(self, link):
        soup = self._downloader(link)
        raise NotImplementedError

    def _journals_cambrige_dealer(self,link):
        soup = self._downloader(link)
        abstract_section = soup.find("a", {"title": "Abstract"})
        inner_soup = self._downloader("http://journals.cambridge.org/action/" + abstract_section["href"])
        target_section = inner_soup.find("p", {"class": "section-title"}, {"text", "Abstract"})
        abstract = target_section.find_next_sibling("p").find_next_sibling("p").contents[0]
        return abstract

    def _ieeexplore_ieee_dealer(self,link):
        soup = self._downloader(link)
        target_section = soup.find("div",{"class":"article"})
        abstract = target_section.p.contents[0]
        return abstract

    def _link_springer_dealer(self, link):
        soup = self._downloader(link)
        target_section = soup.find("h2", {"class":"abstract-heading"})
        abstract = target_section.find_next_sibling("div").p.contents[0]
        abstract = clean(abstract)
        return abstract

    def _arxiv_dealer(self,link):
        soup = self._downloader(link)
        target_section = soup.find("blockquote")
        abstract = target_section.contents[2]
        return abstract

    def _library_wur_dealer(self, link):
        pass

    def _eprints_pascal_networking_dealer(self, link):
        soup = self._downloader(link)
        target_section = soup.find("p", {"class":"abstext"})
        abstract = target_section.contents[0]
        return abstract

    def _paper_ssrn_dealer(self,link):
        soup = self._downloader(link)
        target_section = soup.find("div",{"id": "abstract"})
        abstract = target_section.contents[0]
        return abstract

    def _biomedcentral_dealer(self,link):
        try:
            soup = self._downloader(link)
            target_section = soup.find("h3", text="Abstract").find_next_sibling("div").find_all("p")
            abstract = ""
            for p in target_section:
                abstract = abstract + p.contents[0]
            abstract = clean(abstract)
        except Exception, e:
            print e
        return abstract

    def _igi_global_dealer(self, link):
        pass


class TestWebsiteExtractorFunctions(unittest.TestCase):
    def setUp(self):
        self._dl_acm_dealer_link = "http://dl.acm.org/citation.cfm?id=2514920"
        self._music_ir_dealer_link = "http://www.music-ir.org/mirex/abstracts/2011/ALL1.pdf"
        self._reserchgate_dealer_link = "http://www.researchgate.net/publication/259263486_Information-Seeking_Behaviors_of_Computer_Scientists_Challenges_for_Electronic_Literature_Search_Tools/file/9c96052d4104980195.pdf"
        self._citeseerx_dealer_link = "http://citeseerx.ist.psu.edu/viewdoc/download?doi=10.1.1.176.7544&rep=rep1&type=pdf"
        self._journals_cambrige_dealer_link = "http://journals.cambridge.org/production/action/cjoGetFulltext?fulltextid=7911787"
        self._ieeexplore_ieee_dealer_link = "http://ieeexplore.ieee.org/xpls/abs_all.jsp?arnumber=4076466"
        self._link_springer_dealer_link = "http://link.springer.com/chapter/10.1007/978-3-642-38980-1_27"
        self._arxiv_dealer_link = "http://arxiv.org/abs/1312.3245"
        self._library_wur_dealer_link = "http://library.wur.nl/WebQuery/clc/2033630"
        self._paper_ssrn_dealer_link = "http://papers.ssrn.com/sol3/papers.cfm?abstract_id=1987483"
        self._biomedcentral_dealer_link = "http://www.biomedcentral.com/1471-2105/8/S2/S9"
        self._igi_global_dealer_link = "http://www.igi-global.com/article/content/66354"
        self._secience_direct_dealer_link = "http://www.sciencedirect.com/science/article/pii/S0167947308003484"
        self._pnas_dealer_link = "http://www.pnas.org/content/105/16/6097.short"
        self._epubs_sism_dealer_link = "http://epubs.siam.org/doi/abs/10.1137/1.9781611972764.33"
        self._helda_helsinki_dealer_link = "https://helda.helsinki.fi/handle/10138/38192"
        self._project_euclide_dealer_link = "http://projecteuclid.org/euclid.ss/1399645727"
        self._nature_dealer_link = "http://www.nature.com/ng/journal/v46/n3/abs/ng.2895.html"
        self._degruyter_dealer_link = "http://www.degruyter.com/view/j/sagmb.2014.13.issue-1/sagmb-2013-0031/sagmb-2013-0031.xml"
        self._online_library_wiley_dealer_link = "http://onlinelibrary.wiley.com/doi/10.1002/cem.2566/full"
        self._aaai_deaker_link = ""
        self._bioinformatics_oxfordjournals_dealer_link = ""
        self._dx_plos_dealer_link = ""
        self._mitpressjournals_dealer_link = ""
        self._hjp_dealer_link = ""
        self._website_extractor = WebsiteExtractor()

    def test_dl_acm_dealer(self):
        """
        This function checks whether dl_acm_dealer function returns correct abstract
        It checks two properties of function. At first the function need to return a string.
        Secondly, the returned string must be more than zeros length
        @param self point to class
        """
        abstract = self._website_extractor._dl_acm_dealer(self._dl_acm_dealer_link)
        abstract = sub('\s+', ' ', abstract).strip()
        print abstract

    def test_science_direct_dealer(self):
        abstract = self._website_extractor._science_direct_dealer(self._secience_direct_dealer_link)
        abstract = sub('\s+', ' ', abstract).strip()
        print abstract

    # def test_pnas_dealer(self):
    #     abstract = self._website_extractor._pnas_dealer(self._secience_direct_dealer_link)
    #     abstract = sub('\s+', ' ', abstract).strip()
    #     print abstract
    #     raise NotImplementedError

    def test_epubs_sism_dealer(self):
        abstract = self._website_extractor._epubs_sism_dealer(self._epubs_sism_dealer_link)
        abstract = sub('\s+', ' ', abstract).strip()
        print abstract

    def test_helda_helsinki_dealer(self):
        abstract = self._website_extractor._helda_helsinki_dealer(self._helda_helsinki_dealer_link)
        abstract = sub('\s+', ' ', abstract).strip()
        print abstract

    def test_project_euclide_dealer(self):
        abstract = self._website_extractor._project_euclide_dealer(self._project_euclide_dealer_link)
        abstract = sub('\s+', ' ', abstract).strip()
        print abstract

    def test_nature_dealer(self):
        abstract = self._website_extractor._nature_dealer(self._nature_dealer_link)
        import re
        re.compile(r'')
        cleanre =re.compile('<.*?>')
        abstract = re.sub(cleanre, '', abstract)
        abstract = sub('\s+', ' ', abstract).strip()
        print abstract

    def test_degruyter_dealer(self):
        abstract = self._website_extractor._degruyter_dealer(self._degruyter_dealer_link)
        abstract = sub('\s+', ' ', abstract).strip()
        print abstract

    def test_onine_library_wiley_dealer(self):
        abstract = self._website_extractor._online_library_wiley_dealer(self._online_library_wiley_dealer_link)
        abstract = sub('\s+', ' ', abstract).strip()
        print abstract

    # def test_liebertpub_dealer(self):
    #     abstract = self._website_extractor._liebertpub_dealer(self._liebertpub_dealer_link)
    #     abstract = sub('\s+', ' ', abstract).strip()
    #     print abstract


    def test_aaai_deaker(self):
        abstract = self._website_extractor._liebertpub_dealer(self._liebertpub_dealer_link)
        abstract = sub('\s+', ' ', abstract).strip()
        print abstract

    # def test_bioinformatics_oxfordjournals_dealer(self):
    #     raise NotImplementedError
    #
    # def test_dx_plos_dealer(self):
    #     raise NotImplementedError
    #
    # def test_mitpressjournals_dealer(self):
    #     raise NotImplementedError
    #
    # def test_hjp_dealer(self):
    #     raise NotImplementedError

    def test_ieeexplore_ieee_dealer(self):
        abstract = self._website_extractor._ieeexplore_ieee_dealer(self._ieeexplore_ieee_dealer_link)
        abstract = sub('\s+', ' ', abstract).strip()
        print abstract

    def test_journals_cambrige_dealer(self):
        abstract = self._website_extractor._journals_cambrige_dealer(self._journals_cambrige_dealer_link)
        abstract = sub('\s+', ' ', abstract).strip()
        print abstract

    def test_link_springer_dealer(self):
        abstract = self._website_extractor._link_springer_dealer(self._link_springer_dealer_link)
        abstract = sub('\s+', ' ', abstract).strip()
        print abstract

    def test_arxiv_dealer(self):
        abstract = self._website_extractor._arxiv_dealer(self._arxiv_dealer_link)
        abstract = sub('\s+', ' ', abstract).strip()
        print abstract

    def test_paper_ssrn_dealer(self):
        abstract = self._website_extractor._paper_ssrn_dealer(self._paper_ssrn_dealer_link)
        abstract = sub('\s+', ' ', abstract).strip()
        print abstract

    def test_biomedcentral_dealer(self):
        abstract = self._website_extractor._biomedcentral_dealer(self._biomedcentral_dealer_link)
        abstract = sub('\s+', ' ', abstract).strip()
        print abstract


class AbstractExtractor():
    """
    Class :  AbstractExtractor
    Description:  This class deals with extracting abstract from different website.
    It read the links from database and process fetch iterator(curcor of data). After
    it extracts the data, it will store the information in table "PaperAbstract".
    """
    def __init__(self, mm=None):
        self._db_name = "PaperAbstract"
        self._mm = None
        if mm is not None:
            self._mm = mm
        # Name of table which stores abstract of paper.
        self._info_db_name = "Paper_Links"
        self._website_extractor = WebsiteExtractor()

    @property
    def db_name(self):
        return self._db_name

    @property
    def db_info_name(self):
        return self._info_db_name

    def download_data(self, database_name=None):
        """
        This function is in charge of receiving data from a specific database.
        """
        if None == database_name:
            database_name = self._info_db_name
        sql = "select PaperLinks.Link_ID,PaperLinks.Paper_ID, Persons.FirstName,Persons.LastName," \
              " PaperLinks.PaperLink, PaperNames.PaperName from PaperLinks, PaperNames,Persons" \
              " where PaperNames.Paper_ID = PaperLinks.Paper_ID and PaperNames.P_ID = Persons.ID;"
        self._mm.execute_sql(sql)

        # iterator over returned values
        iter = self._mm.fetch()

        abstract_file_obj = open("abstract.xml", "w")
        abstract_file_obj.write("<articles>")
        for row in iter:
            abstract = self._analyze_website(row)
            if abstract is not None:
                abstract_file_obj.write("<Article>" + "\n")
                abstract_file_obj.write("<number>" + "\n")
                abstract_file_obj.write(str(row[1] )+ "\n")
                abstract_file_obj.write("</number>" + "\n")
                abstract_file_obj.write("<name>" )
                # write first name 
                abstract_file_obj.write(row[2])
                # write last name
                abstract_file_obj.write(row[3])
                abstract_file_obj.write("<title>" + "\n")
                abstract_file_obj.write(row[4])
                abstract_file_obj.write("</title>")
                abstract_file_obj.write("</number>" + "\n")
                abstract_file_obj.write("<abstract>""\n")
                abstract_file_obj.write(abstract.encode('utf-8'))
                abstract_file_obj.write("</abstract>" + "\n")
                abstract_file_obj.write("</Article>")
                abstract_file_obj.write("\n")
            #sleep(randint(10, 20))

        abstract_file_obj.write("</articles>")
        abstract_file_obj.close()
        return iter

    def pdf_abstract_extractor(self, pdf):
        def __pdf_to_txt(pdf_path):
            null_f = open(devnull, "w")
            contents = Popen(["ps2ascii", pdf_path], stdout=PIPE, stderr=null_f).communicate()[0]
            null_f.close()
            abstract_start_position = contents.lower().find("abstract")
            abstract_end_position = contents[abstract_start_position:].lower().find("\n\n") + abstract_start_position
            len_abstract = len("abstract") + len('\n')
            return sub('\s+', ' ', contents[abstract_start_position + len_abstract:abstract_end_position]).strip()
        contents = None
        try:
            print pdf
            contents = __pdf_to_txt(pdf)
        except Exception, e:
            stderr.write("Debug: path, %s" % pdf)
            stderr.write("Error: %s,\n" % e)
        return contents

    def _analyze_website(self, row):
        link_id = row[0]
        paper_id = row[1]
        first_name = row[2].lstrip().decode('latin1')
        last_name = row[3].lstrip().decode('latin1')
        paper_link = row[4]
        paper_name = row[5]
        folder_prefix = "../../../docs/papers/"
        path_name = folder_prefix + first_name + '_' + last_name + "/" + paper_name
        contents = None

        if "pdf" in paper_link:
            try:
                from urllib import urlretrieve
                urlretrieve(paper_link, path_name)
                contents = self.pdf_abstract_extractor(path_name)
            except Exception, e:
                stderr.write("Error: %s .\n" % e)
            pass
        else:

            try:
                processed_link = paper_link.split("/")
                web_site = processed_link[2]
                contents = self._website_extractor.website_extractor(web_site, paper_link)
                print "Downloaded: [ link id: %s, paper_id: %s. (link: %s)]." % (link_id, paper_id, paper_link)
            except Exception, e:
                stderr.write("Error: %s, link id: %s, paper id: %s. (link: %s). \n" % (e, link_id, paper_id, paper_link))
        return contents

if __name__ == "__main__":
    mysql_db = MysqlMessager()
    abstract_extractor = AbstractExtractor(mysql_db)
    abstract_extractor.download_data()

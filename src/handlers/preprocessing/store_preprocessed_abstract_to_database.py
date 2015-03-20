"""
This file is for storing pickle file to database.

Step of pre-processing is like this

1. extract abstract link from website
2. download abstract from links
3. store them in a xml file
4. extract keywords from xml and store them in a pickle file.
5. combine all keywords to form new abstract using csv form
6. store abstract in database
7. store newly formed abstract in database

this file implements the 7 step

"""
from sys import stderr
from pickle import load
from contextlib import contextmanager
from MySQLdb import connect
from MySQLdb import Error as MysqldbError


def execute_sql(sql_, database_):
    try:
        cursor = database_.cursor()
        cursor.execute(sql_)
        database_.commit()
    except MysqldbError, e:
        # Rollback in case there is any error
        print >> stderr, e
        database_.rollback()


@contextmanager
def read_pickle_file(pickle_file_path):
    """
    This file reads information according from a pickler file path and return the content.
    """
    try:
        with open(pickle_file_path) as f:
            yield load(f)
    except IOError, e:
        print >> stderr, e
    finally:
        pass


if __name__ == "__main__":
    database = connect(host="localhost", user="root", passwd="kid1412", db="keyword_app")
    clean_database_sql = "truncate table PreprocessedAbstracts;"
    execute_sql(clean_database_sql, database)
    file_path = "../../keywords/corpus_abstract_109.txt"
    with read_pickle_file(file_path) as content:
        print len(content)
        for i in xrange(len(content)):
            sql = "insert into PreprocessedAbstracts values(default, \"%s\")" % content[i]
            execute_sql(sql, database)

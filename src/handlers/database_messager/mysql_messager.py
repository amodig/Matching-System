
import MySQLdb
import time
import codecs

class MysqlMessager():
    """
    Class :  MySQLMessager
    Description:  MySQL Messager: handles communication with MySQL server.
    """    
    # def __init__(self,table = None,  user="keyword_app", password="ohTun1ah", database = "matching_system"):
    def __init__(self, table=None, user="root", password="root", database="matching_system"):
        """ Initialize database connection, open logfile
        @param self Pointer to class
        @param user User name
        @param password User password
        @param database Name of database
        """

        self.table = table
        self.mysql_log_file = codecs.open("mysql_log_file.txt", "w","utf-8")
        try:
            self.cnx = MySQLdb.connect('localhost', user, password, database)
            self.cursor = self.cnx.cursor()  
        except Exception, e:
            print "Error: %s" % (e.args[0])
        
    def clear_table(self,  **kwargs):
        """ Clear table stored in variable table
        @param self Pointer to class
        @param table Name of table
        """
        table = kwargs.get('table', self.table)
        if table is not None:
            sql = u"TRUNCATE TABLE %s;"%table
            self.execute_sql(sql, self.mysql_log_file)

    def execute_sql(self, sql, log_file=None):
        """ Execute SQL, if it is failed and log file name is given, store the information in log file
        @param self Pointer to class
        @param log_file Name of log file used to store error information
        """
        try:
            self.cursor.execute(sql)
            self.cnx.commit()
        except Exception, e:
            # Rollback in case there is any error
            self.cnx.rollback()
            log = "Error %s -> %s" % (e.args[0], e.args[1])
            if log_file is not None:
                log_file.write(time.asctime(time.localtime(time.time())) + log + '\n')
            else:
                print log

    def fetch(self):
        return self.cursor

    def __del__(self):
        """ Close the cursor, disconnect the database and close the log file.
        @param self Pointer to class
        """
        if 'cursor' in self.__dict__.keys():
            self.cursor.close()
        if 'cnx' in self.__dict__.keys():
            self.cnx.close()
        if 'mysql_log_file' in self.__dict__.keys():
            self.mysql_log_file.close()

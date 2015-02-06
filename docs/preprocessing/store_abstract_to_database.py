import xmltodict
import json
import MySQLdb

def excute_sql(sql, cursor, database):
    """ Excute sql, if it is failed and log file name is given, store the information in log file
    @param self Pointer to class
    @param log_file_name Name of log file used to store error information
    """
    try:
        cursor.execute(sql)
        database.commit()
    except Exception, e:
        # Rollback in case there is any error
        database.rollback()

with open("abstracts.xml") as f:
    
    content = f.read()
    articles = xmltodict.parse(content)
    db = MySQLdb.connect(host="localhost", # your host, usually localhost
                         user="root", # your username
                          passwd="kid1412", # your password
                          db="keyword_app") # name of the data base
    cur = db.cursor()
        
    for article in articles["articles"].values()[0]:
        name = article["name"].encode("utf8").replace('"', '\\"')
        title = article["title"].encode("utf8").replace('"', '\\"')
        abstract = article["abstract"].encode("utf8").replace('"', '\\"')
        sql = "insert into Abstracts values(default,\"%s\",\"%s\",\"%s\");"%( name, title, abstract)
        excute_sql(sql, cur, db)

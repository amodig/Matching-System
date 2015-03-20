import MySQLdb
import xmltodict


def execute_sql(sql, cursor, database):
    try:
        cursor.execute(sql)
        database.commit()
    except Exception, e:
        # Rollback in case there is any error
        database.rollback()

with open("abstracts.xml") as f:
    content = f.read()
    articles = xmltodict.parse(content)
    db = MySQLdb.connect(host="localhost", user="root", passwd="kid1412", db="keyword_app")
    cursor = db.cursor()
        
    for article in articles["articles"].values()[0]:
        name = article["name"].encode("utf8").replace('"', '\\"')
        title = article["title"].encode("utf8").replace('"', '\\"')
        abstract = article["abstract"].encode("utf8").replace('"', '\\"')
        sql = "insert into Abstracts values(default,\"%s\",\"%s\",\"%s\");" % (name, title, abstract)
        execute_sql(sql, cursor, db)

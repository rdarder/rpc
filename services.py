import random
import gevent
import db


def setup_services():
  services = {}
  services['db'] = DB(db.DBPool('sample_db.sqlite', 10, 'sqlite3'))
  services['math'] = Math()
  return services


class Math(object):
  def fast_add(self, a, b):
    return a + b

  def slow_add(self, a, b):
    gevent.sleep(5)
    return a + b


class DB(object):
  def __init__(self, pool):
    self.pool = pool

  def list_tables(self):
    cursor = self.query('select name from sqlite_master where type="table"')
    for row in cursor.fetchall():
      yield row[0]

  def get_create(self, table):
    sql = ("select sql from sqlite_master where type='table' and name = '{}'"
           .format(table))
    cursor = self.query(sql)
    return cursor.fetchall()[0][0]

  def get_all_rows(self, table):
    return self.query('select * from {}'.format(table))

  def query(self, query):
    gevent.sleep(random.randint(1,5))
    conn = self.pool.get()
    cursor = conn.cursor()
    cursor.execute(query)
    return cursor


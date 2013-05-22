import os
import gevent
import db
from rpc.json_encoder import encoder_for


def setup_services():
  """
  Setup services for this module. This function is called by the rpc server
  for getting a name to instance mapping of the exposed services.
  :return: a map of names to objects. The object non special methods will be
  exposed via rpc.
  """
  current_dir = os.path.dirname(__file__)
  services = {}
  services['db'] = DB(db.DBPool(os.path.join(
    current_dir, 'sample_db.sqlite'), 10, 'sqlite3'))
  services['math'] = Math()
  return services


@encoder_for(db.DBCursor)
def encode(cursor):
  """Tell the rpc server encoder how to convert a DBCursor to json."""
  return {
    'header': [desc[0] for desc in cursor.description],
    'rows': cursor.fetchall()
  }


class Math(object):
  """
  Simple Math service. It has two methods that implements addition. slow_add
  is useful for testing how rpc calls may have an arbitrary response time
  without blocking other calls.
  """

  def fast_add(self, a, b):
    return a + b

  def slow_add(self, a, b):
    gevent.sleep(5)
    return a + b


class DB(object):
  """
  Sample Service for that makes simple queries upon a sample database. Meant
  to be used upon a sqlite database.
  """

  def __init__(self, pool):
    self.pool = pool

  def list_tables(self):
    """List the existing tables.
    :rtype: generator of strings
    """
    cursor = self.query('select name from sqlite_master where type="table"')
    for row in cursor.fetchall():
      yield row[0]

  def get_create(self, table):
    """Get the schema for a given table name.
    :rtype: basestring
    """
    sql = ("select sql from sqlite_master where type='table' and name = '{}'"
           .format(table))
    cursor = self.query(sql)
    #we have a cursor with only one row and only one column. just return the
    # cell value.
    return cursor.fetchall()[0][0]

  def get_all_rows(self, table):
    """Make a table listing.
    :rtype: db.DBCursor
    """
    return self.query('select * from {}'.format(table))

  def query(self, query):
    """Issue a user defined query.
    :rtype: db.DBCursor
    """
    conn = self.pool.get()
    cursor = conn.cursor()
    cursor.execute(query)
    return cursor


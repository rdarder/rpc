import json
from geventwebsocket import WebSocketError
import webob, webob.dec, webob.static
import gevent
from gevent import pywsgi
from geventwebsocket.handler import WebSocketHandler
from json_encoder import RegistryJsonEncoder
import db


class Math(object):
  def fast_add(self, a, b):
    return a + b

  def slow_add(self, a, b):
    gevent.sleep(5)
    return a + b


class DB(object):
  def __init__(self, pool):
    self.pool = pool

  def get_artists(self):
    cursor = self.pool.get().cursor()
    cursor.execute('select * from Artist')
    return cursor

  def issue_sql(self, query):
    conn = self.pool.get()
    cursor = conn.cursor()
    cursor.execute(query)
    return cursor


class JsonRpcServer(object):
  def __init__(self, services, encoder, decoder):
    self.services = services
    self.encoder = encoder
    self.decoder = decoder

  def server_loop(self, websocket):
    while True:
      try:
        message = websocket.receive()
        gevent.spawn(self.handle_message, websocket, message)
      except WebSocketError:
        break

  def handle_message(self, websocket, message):
    call_spec = self.decoder.decode(message)
    call_id = call_spec.get('id')
    if call_id is None:
      return
    try:
      result = self.handle_rpc(call_id, call_spec)
      wrapped = dict(success=True, result=result, id=call_id)
      encoded = self.encoder.encode(wrapped)
      websocket.send(encoded)
    except BaseException, e:
      wrapped = dict(success=False, error=dict(message=e.message,
                                               type=type(e).__name__))
      websocket.send(self.encoder.encode(wrapped))


  def handle_rpc(self, call_id, call_spec):
    service = call_spec.get('service', '')
    method = call_spec.get('method', '')
    args = call_spec.get('args', [])
    kwargs = call_spec.get('kwargs', {})
    service_instance = self.services.get(service, None)
    if service_instance is None:
      return dict(success=False, id=call_id,
                  error=dict(message="invalid service name"))
    method_instance = getattr(service_instance, method, None)
    if method_instance is None or not callable(method_instance):
      return dict(success=False, id=call_id,
                  error=dict(message="invalid method name"))
    return method_instance(*args, **kwargs)


class WebServer(object):
  def __init__(self, rpc_server):
    self.static_files = webob.static.DirectoryApp('web_client')
    self.rpc_server = rpc_server

  @webob.dec.wsgify
  def handler(self, request):
    """
    :type request: webob.Request
    """
    root = request.path_info_peek().lstrip('/')
    if root == 'client':
      request.path_info_pop()
      return self.static_files(request)
    elif root == 'rpc':
      websocket = request.environ['wsgi.websocket']
      self.rpc_server.server_loop(websocket)


#gevent / geventwebsocket logging error fix
def log_request(self):
  log = self.server.log
  if log:
    if hasattr(log, "info"):
      log.info(self.format_request() + '\n')
    else:
      log.write(self.format_request() + '\n')


gevent.pywsgi.WSGIHandler.log_request = log_request

handler = None


def setup_services():
  services = {}
  services['db'] = DB(db.DBPool('sample_db.sqlite', 10, 'sqlite3'))
  services['math'] = Math()
  return services


def main(run_server):
  global handler
  services = setup_services()
  encoder = RegistryJsonEncoder(sort_keys=True, indent=2)
  rpc_server = JsonRpcServer(services, encoder, json.JSONDecoder())
  web_server = WebServer(rpc_server)
  handler = web_server.handler
  if run_server:
    server = pywsgi.WSGIServer(("", 8000), handler,
                               handler_class=WebSocketHandler)
    server.serve_forever()


main(__name__ == '__main__')


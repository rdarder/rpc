import json
import webob, webob.dec, webob.static
import gevent


class Service1(object):
  def fast_add(self, a, b):
    return a + b

  def slow_add(self, a, b):
    gevent.sleep(5)
    return a + b


class JsonRpcServer(object):
  def __init__(self, services):
    self.services = services

  def server_loop(self, websocket):
    while True:
      message = websocket.receive()
      gevent.spawn(self.handle_message, message)

  def handle_message(self, websocket, message):
    call_spec = json.loads(message)
    call_id = call_spec['id']
    service = call_spec['service']
    method = call_spec['method']
    args = call_spec['args'] or []
    kwargs = call_spec['kwargs'] or {}
    service_instance = self.services.get(service, None)
    if service_instance is None:
      return dict(success=False, id=call_id,
                  error=dict(message="invalid service name"))
    method_instance = getattr(service_instance(method, None))
    if method_instance is None or not callable(method_instance):
      return dict(success=False, id=call_id,
                  error=dict(message="invalid method name"))
    try:
      result = method_instance(*args, **kwargs)
      wrapped = dict(success=True, result=result, id=call_id)
      encoded = json.dumps(wrapped)
      websocket.send(encoded)
    except BaseException, e:
      wrapped = dict(success=False, error=dict(message=e.message, exception=e))
      websocket.send(json.dumps(wrapped))


class WebServer(object):
  def __init__(self, rpc_server):
    self.static_files = webob.static.DirectoryApp('web_client')
    self.rpc_server = rpc_server

  @webob.dec.wsgify
  def handler(self, request):
    """
    :type request: webob.Request
    """
    root = request.path_info.lstrip('/')
    if root == '/client':
      request.path_info_pop()
      return self.static_files(request)
    elif root == 'rpc':
      websocket = request.environ['wsgi.websocket']
      gevent.spawn(self.rpc_server.server_loop, websocket)


services = {'service1': Service1()} #register more services in here
rpc_server = JsonRpcServer(services)
web_server = WebServer(rpc_server)

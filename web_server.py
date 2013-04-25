import json
import os
from traceback import extract_tb
from geventwebsocket import WebSocketError
import sys
import webob, webob.dec, webob.static, webob.exc
import gevent
from gevent import pywsgi
from geventwebsocket.handler import WebSocketHandler
from json_encoder import RegistryJsonEncoder
import db


class ErrorHandler(object):
  def __init__(self, root, user_filenames):
    self.filename_mapping = {}
    for user_filename in user_filenames:
      if user_filename.endswith('.pyc'):
        user_filename = user_filename[:-1]

      if user_filename.startswith(root):
        mapped_filename = user_filename[len(root):]
      else:
        mapped_filename = user_filename

      self.filename_mapping[user_filename] = mapped_filename

  def format_trace(self, traceback):
    formatted = []
    for filename, line_number, function_name, code in extract_tb(traceback):
      if filename in self.filename_mapping:
        formatted.append(dict(filename=self.filename_mapping[filename],
                              line=line_number, function=function_name,
                              code=code))
    return formatted

  def get_error_response(self):
    exception_type, value, traceback = sys.exc_info()
    return dict(success=False,
                error=dict(type=exception_type.__name__,
                           message=value.message,
                           traceback=self.format_trace(traceback))
    )


class JsonRpcServer(object):
  last_resort_response = {'success': False, 'error': {'type': 'internal'}}

  def __init__(self, services, encoder, decoder, error_handler):
    self.services = services
    self.encoder = encoder
    self.decoder = decoder
    self.error_handler = error_handler

  def server_loop(self, websocket):
    while True:
      try:
        message = websocket.receive()
        if message is None:
          break
        gevent.spawn(self.handle_message, websocket, message)
      except WebSocketError:
        break

  def handle_message(self, websocket, message):
    call_spec = self.decoder.decode(message)
    call_id = call_spec.get('id')
    if call_id is None:
      return
    response = self.last_resort_response
    try:
      result = self.handle_rpc(call_id, call_spec)
      response = dict(success=True, result=result)
    except:
      response = self.error_handler.get_error_response()
    finally:
      response['id'] = call_id
      encoded = self.encoder.encode(response)
      websocket.send(encoded)


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
    self.static_files = webob.static.DirectoryApp('client')
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
    elif root == '':
      return webob.exc.HTTPMovedPermanently(location='/client')


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


def setup_modules(module_names):
  services = {}
  filenames = []
  for module_name in module_names:
    module = __import__(module_name)
    filenames.append(module.__file__)
    mod_services = module.setup_services()
    services.update(mod_services)
  return services, filenames


def main(run_server, module_names):
  global handler
  services, filenames = setup_modules(module_names)
  encoder = RegistryJsonEncoder(sort_keys=True, indent=2)
  error_handler = ErrorHandler(os.path.dirname(__file__) + '/', filenames)
  decoder = json.JSONDecoder()
  rpc_server = JsonRpcServer(services, encoder, decoder, error_handler)
  web_server = WebServer(rpc_server)
  handler = web_server.handler
  if run_server:
    server = pywsgi.WSGIServer(("", 8000), handler,
                               handler_class=WebSocketHandler)
    server.serve_forever()


if __name__ == '__main__':
  main(run_server=True, module_names=['services'])


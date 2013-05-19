import json
import os
from geventwebsocket import WebSocketError
import gevent
from rpc.errors import ErrorHandler
from rpc.json_encoder import RegistryJsonEncoder
from rpc.service_loader import setup_modules

class RpcServer(object):
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


def build_rpc_server(module_names):
  services, filenames = setup_modules(module_names)
  encoder = RegistryJsonEncoder(sort_keys=True, indent=2)
  decoder = json.JSONDecoder()
  error_handler = ErrorHandler(os.path.dirname(__file__) + '/', filenames)
  return RpcServer(services, encoder, decoder, error_handler)


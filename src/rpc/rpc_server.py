import json
import os
from geventwebsocket import WebSocketError
import gevent
from rpc.errors import ErrorHandler
from rpc.json_encoder import RegistryJsonEncoder
from rpc.service_loader import setup_modules


class RpcServer(object):
  """Rpc Server over websockets. Given an open websocket,
  receives rpc messages and routes them to the existing services,
  returning a wrapped json response.
  The format of a call is a json object with the following properties:
  id: some unique identifier across all the other calls from the same client,
  service: the name of the service the client is calling.
  method: the service method's name
  args: an (optional) list of positional arguments
  kwargs: an (optional) mapping of keyword arguments
  """

  #a canned response if we can't even generate a proper error response
  # without raising an exception.
  last_resort_response = {'success': False, 'error': {'type': 'internal'}}

  def __init__(self, services, encoder, decoder, error_handler):
    """
    Setup the rpc server.
    :param services: mapping of names to service instances
    :type services: dictionary
    :param encoder: a json encoder (common case is to get a
    RegistryJsonEncoder)
    :type encoder: json.JSONEncoder
    :param decoder: a json decoder
    :type decoder:  json.JSONDecoder
    :param error_handler: an error handler for generating a response upon an
    unhandled exception
    :type error_handler: errors.ErrorHandler
    """
    self.services = services
    self.encoder = encoder
    self.decoder = decoder
    self.error_handler = error_handler

  def server_loop(self, websocket):
    """Wait for incoming messages while the websocket is open,
    and process those messages in a separate coroutine.
    """
    while True:
      try:
        message = websocket.receive()
        if message is None:
          break
        gevent.spawn(self.handle_message, websocket, message)
      except WebSocketError:
        break

  def handle_message(self, websocket, message):
    """Handle an individual rpc message, decoding it and delegating to
    handle_rpc client. The return value from handle_rpc is wrapped in a
    response message and sent via the client websocket.
    :param websocket: the websocket where this server is sending the response.
    :param message: the raw payload of the message
    """
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
    """Handle an rpc message, already decoded and available as a dictionary.
    Dispatches the message as an actual python function call and returns
    whatever the service returns.
    :param: call_id: the call identifier
    :param: call_spec: the dictionary representing the rpc message
    :type call_spec: dictionary
    """
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
  """Build an rpc server for the usual scenario"""
  services, filenames = setup_modules(module_names)
  encoder = RegistryJsonEncoder(sort_keys=True, indent=2, encoding='latin1')
  decoder = json.JSONDecoder()
  error_handler = ErrorHandler(os.path.dirname(__file__) + '/', filenames)
  return RpcServer(services, encoder, decoder, error_handler)


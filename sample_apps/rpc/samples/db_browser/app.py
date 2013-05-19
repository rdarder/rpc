import argparse
import gevent.pywsgi
from geventwebsocket import WebSocketHandler
from geventwebsocket.websocket import WebSocket
from rpc.rpc_server import build_rpc_server
from rpc.web_handlers import SimpleRouting, PackageAssets, WebSocketSpawn


def build_app():
  app = SimpleRouting()
  rpc_server = build_rpc_server(['rpc.samples.db_browser.services'])
  app.register_route('rpc', WebSocketSpawn(rpc_server))
  app.register_route('lib', PackageAssets('rpc', 'clients'))
  app_assets = PackageAssets('rpc.samples.db_browser', 'client')
  app.register_route('client', app_assets)
  app.register_redirect('/', '/client/index.html')
  return app


def cmdline_parser():
  parser = argparse.ArgumentParser()
  parser.add_argument('--port', type=int, default=8000)
  return parser


def main():
  args = cmdline_parser().parse_args()
  server = gevent.pywsgi.WSGIServer(("", args.port), build_app(),
                                    handler_class=WebSocketHandler)
  server.serve_forever()


if __name__ == '__main__':
  main()

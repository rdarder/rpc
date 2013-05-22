import argparse
import gevent.pywsgi
from geventwebsocket import WebSocketHandler
from rpc.rpc_server import build_rpc_server
from rpc.web_handlers import (SimpleRouting, PackageAssets, WebSocketSpawn,
                              RequirementAssets)


def build_app():
  #build the main web app
  app = SimpleRouting()

  #build the rpc server, exposing services from our 'services' module
  rpc_server = build_rpc_server(['rpc.samples.db_browser.services'])
  #register the rpc server route
  app.register_route('rpc', WebSocketSpawn(rpc_server))
  #serve the rpc client files under '/lib'
  app.register_route('lib', PackageAssets('rpc', 'clients'))
  #serve our own assets, the ones under sample_apps/client/shared under /shared
  #note that we're using RequirementAssets instead of PackageAssets,
  app.register_route('shared',
                     RequirementAssets('rpc-samples', 'client/shared'))

  #serve our own assets, the ones under sample_apps/client/db_browser under
  # /app
  app.register_route('app',
                     RequirementAssets('rpc-samples', 'client/db_browser'))

  #handle the root path redirecting the browser to the home page.
  app.register_redirect('/', '/app/index.html')

  #return the main app with all the previous routes configured
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

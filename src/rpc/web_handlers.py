import mimetypes
import wsgiref.headers
import pkg_resources
import webob, webob.static, webob.exc
import gevent
import gevent.pywsgi


class WebSocketSpawn(object):
  def __init__(self, server):
    self.rpc_server = server

  def __call__(self, environ, start_response):
    websocket = environ.get('wsgi.websocket')
    if websocket is None:
      start_response('400 Bad Request', [('Content-Type', 'text/plain')])
    else:
      self.rpc_server.server_loop(websocket)
      start_response('200 OK', [('Content-Type', 'text/plain')])
      return ['']

#gevent / geventwebsocket logging error fix
def _log_request(self):
  log = self.server.log
  if log:
    if hasattr(log, "info"):
      log.info(self.format_request() + '\n')
    else:
      log.write(self.format_request() + '\n')


gevent.pywsgi.WSGIHandler.log_request = _log_request


class PackageAssets(object):
  BLOCK_SIZE = 1 << 16

  def __init__(self, package_name, base_path):
    self.package_name = package_name
    self.base_path = base_path

  def __call__(self, environ, start_response):
    def set_content_type(status, headers, exc_info=None):
      header_map = wsgiref.headers.Headers(headers)
      header_map['Content-Type'] = mime_type
      start_response(status, headers, exc_info)

    resource_url = environ['PATH_INFO'].lstrip('/')
    resource_path = '/'.join([self.base_path, resource_url])
    mime_type, _ = mimetypes.guess_type(resource_url)
    req_method = environ['REQUEST_METHOD']
    if req_method not in ('GET', 'HEAD'):
      app = webob.exc.HTTPMethodNotAllowed("You cannot %s a file" % req_method)
    else:
      try:
        res = pkg_resources.resource_stream(self.package_name, resource_path)
        if 'wsgi.file_wrapper' in environ:
          app = environ['wsgi.file_wrapper'](res, self.BLOCK_SIZE)
        else:
          app = (webob.Response(app_iter=webob.static.FileIter(res))
                 .conditional_response_app)
      except:
        app = webob.exc.HTTPNotFound()
    return app(environ, set_content_type)


class RequirementAssets(PackageAssets):
  def __init__(self, requirement_name, base_path):
    super(RequirementAssets, self).__init__(
      pkg_resources.Requirement.parse(requirement_name), base_path)


class SimpleRouting(object):
  def __init__(self):
    self.routes = {}
    self.redirects = {}

  def register_redirect(self, src, dst):
    #TODO: check for cycles
    assert src not in self.redirects
    self.redirects[src] = dst

  def register_route(self, route, app):
    assert route not in self.routes
    self.routes[route] = app

  def __call__(self, environ, start_response):
    """
    :type request: webob.Request
    """
    path_info = environ['PATH_INFO']
    if path_info in self.redirects:
      app = webob.exc.HTTPMovedPermanently(location=self.redirects[path_info])
    else:
      path, cut, prefix = self.first_path_segment(path_info)
      root = path[:cut]
      rest = path[cut:]
      if root in self.routes:
        environ['PATH_INFO'] = rest
        environ['SCRIPT_NAME'] = prefix + root
        app = self.routes[root]
      else:
        app = webob.exc.HTTPNotFound()
    return app(environ, start_response)


  def first_path_segment(self, path):
    if not path:
      return None
    slashes = ''
    while path.startswith('/'):
      slashes += '/'
      path = path[1:]
    idx = path.find('/')
    if idx == -1:
      idx = len(path)
    return path, idx, slashes


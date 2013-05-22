import mimetypes
import wsgiref.headers
import pkg_resources
import webob, webob.static, webob.exc
import gevent
import gevent.pywsgi


class WebSocketListener(object):
  """wsgi app that handles a websocket enabled request and delegates it to
  the rpc server.
  """

  def __init__(self, server):
    """
    :type rpc_server: rpc.rpc_server.RpcServer
    """
    self.rpc_server = server

  def __call__(self, environ, start_response):
    websocket = environ.get('wsgi.websocket')
    if websocket is None:
      start_response('400 Bad Request', [('Content-Type', 'text/plain')])
    else:
      self.rpc_server.server_loop(websocket)
      start_response('200 OK', [('Content-Type', 'text/plain')])
      return ['']


def _log_request(self):
  """Temporary fix for a bug in geventwebsocket or pywsgi logging."""
  log = self.server.log
  if log:
    if hasattr(log, "info"):
      log.info(self.format_request() + '\n')
    else:
      log.write(self.format_request() + '\n')


gevent.pywsgi.WSGIHandler.log_request = _log_request


class PackageAssets(object):
  """Wsgi server for static files bundled as part of a python package (see
  setuptools pkg_resources documentation). This handler enables a simple app
  to run in development mode without copying/deploying/linking the static
  files outside the source tree. It doesn't make much sense in a production
  environment, where the assets should be manually packaged and served by a
  static web server.
  Note that setuptools distributions include non python files if the setup()
  call in setup.py if include_package_data==True. This works when installing
  a binary distribution (setup.py bdist or install) or a link distribution (
  setup.py develop), but not for a source distribution (setup.py sdist). For
  having a sdist include the assets, you have to manually edit the MANIFEST
  .in file (see setuptools documentation)
  """
  BLOCK_SIZE = 1 << 16

  def __init__(self, package_name, base_path):
    """Build a Package Assets server. Serve all the assets for a given
    package name which are under a given subdirectory.
    :param package_name: the package holding the assets
    :type pacakge_name: str
    :param base_path: a directory under which the assets are present. Note
    that you can use '/' as a base_path and that would involve serving all
    the package files, _including_ the python source code,
    which may not be what the developer intention.
    """
    self.package_name = package_name
    self.base_path = base_path

  def __call__(self, environ, start_response):
    """ Handle the asset call, getting the package resource and returning its
    contents, or a 404 response in any access error. This is mostly code from
    webob.static.FileApp, but works for package assets instead of just
    filenames.
    Note that because resources/assets may be in a zipped egg,
    we don't just map a resource to a path and handle that as a file,
    but instead get a handle to an open file and return its contents. That
    impairs browser file caching as we don't honour the *Age headers
    """

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
  """Wsgi server for static files bundled as part of a python requirement (see
  setuptools pkg_resources documentation). This is similar to Package assets,
   but instead of referencing a package (which can have many distributions
   and can cause confusion for namespace packages),
   we just refer to a requirement/distribution name.
  """

  def __init__(self, requirement_name, base_path):
    super(RequirementAssets, self).__init__(
      pkg_resources.Requirement.parse(requirement_name), base_path)


class SimpleRouting(object):
  """Minimalistic routing web application. Uses the first url component to
  determine where to delegate the request.  Also bundles simple redirect routes
  The router actually 'consumes' the routing key, meaning it's appended to
  SCRIPT_NAME and removed from PATH_INFO
  """

  def __init__(self):
    self.routes = {}
    self.redirects = {}

  def register_redirect(self, src, dst):
    """Registers a route to be handled as a redirection (useful for serving
    '/')
    """
    #TODO: check for cycles
    assert src not in self.redirects
    self.redirects[src] = dst

  def register_route(self, route, app):
    """Registers a route to be handled by a wsgi application."""
    assert route not in self.routes
    self.routes[route] = app

  def __call__(self, environ, start_response):
    """Handle the request and route it. """
    path_info = environ['PATH_INFO']
    if path_info in self.redirects:
      app = webob.exc.HTTPMovedPermanently(location=self.redirects[path_info])
    else:
      path, cut, prefix = self.first_path_segment(path_info)
      root = path[:cut]
      rest = path[cut:]
      if root in self.routes:
        environ['PATH_INFO'] = rest
        #XXX shouldn't we += to SCRIPT_NAME?
        environ['SCRIPT_NAME'] = prefix + root
        app = self.routes[root]
      else:
        app = webob.exc.HTTPNotFound()
    return app(environ, start_response)


  def first_path_segment(self, path):
    """
    get the first path segment offset of an url, consuming consecutive trailing
    slashes."""
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


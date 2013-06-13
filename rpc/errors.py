from traceback import extract_tb
import sys


class ErrorHandler(object):
  """
  Development mode error handler. Formats an exception traceback for
  generating an rpc error response suitable for displaying it on the client.
  """

  def __init__(self, root, user_filenames):
    """
    :param root: the root directory of the rpc package. This handler will
    strip this path from errors that occur under this package.
    :type root: str
    :param user_filenames: The file paths of the configured services.
    :type user_filenames: list of str
    """
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
    """
    Format a traceback for sending it to the client. Only show application
    errors, stripping frames belonging to system or 3rd party libs.
    """
    formatted = []
    for filename, line_number, function_name, code in extract_tb(traceback):
      if filename in self.filename_mapping:
        formatted.append(dict(filename=self.filename_mapping[filename],
                              line=line_number, function=function_name,
                              code=code))
    return formatted

  def get_error_response(self):
    """Build an rpc error response based on the latest exception."""
    exception_type, value, traceback = sys.exc_info()
    return dict(success=False,
                error=dict(type=exception_type.__name__,
                           message=value.message,
                           traceback=self.format_trace(traceback))
    )


from traceback import extract_tb
import sys


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


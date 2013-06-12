from setuptools import setup
import os

def find_extra_files(path):
  for dirpath, _, filenames in os.walk(path):
    if len(filenames) > 0:
      yield (dirpath, [os.path.join(dirpath, filename)
                       for filename in filenames])

setup(
  name='rpc',
  version='0.2',
  packages=['rpc'],
  namespace_packages=['rpc'],
  data_files=find_extra_files('clients'),
  url='http://github.com/rdarder/rpc',
  install_requires=['gevent', 'gevent-websocket', 'webob' ],
  license='GPL',
  author='rdarder',
  author_email='darder@gmail.com',
  description='python async rpc server / angularjs client. Json encoded and '
              'websockets as transport.'
)

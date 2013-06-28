from setuptools import setup
import os


def find_extra_files(path):
  return [
    (dirpath, [os.path.join(dirpath, filename) for filename in filenames])
    for dirpath, _, filenames in os.walk(path)
  ]

setup(
  name='rpc',
  version='0.3',
  packages=['rpc'],
  namespace_packages=['rpc'],
  data_files=find_extra_files('clients'),
  url='http://github.com/rdarder/rpc',
  install_requires=['cython', 'gevent>=1.0dev', 'gevent-websocket', 'webob'],
  license='GPL',
  author='rdarder',
  author_email='darder@gmail.com',
  description='python async rpc server / angularjs client. Json encoded and '
              'websockets as transport.',
  dependency_links=[
    'https://github.com/surfly/gevent/archive/1.0rc2.tar.gz#egg=gevent-1.0dev'
  ]
)

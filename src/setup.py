from setuptools import setup

setup(
  name='rpc',
  version='0.2',
  packages=['rpc'],
  namespace_packages=['rpc'],
  include_package_data=True,
  url='http://github.com/rdarder/rpc',
  install_requires=['gevent', 'gevent-websocket', 'webob' ],
  license='GPL',
  author='rdarder',
  author_email='darder@gmail.com',
  description='python async rpc server / angularjs client. bundled with a small demo app. json encoded and websocket as transport.'
)

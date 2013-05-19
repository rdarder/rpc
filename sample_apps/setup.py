from setuptools import setup

setup(
  name='rpc-samples',
  version='0.2',
  packages=['rpc'],
  namespace_packages=['rpc'],
  include_package_data=True,
  url='http://github.com/rdarder/rpc',
  install_requires=['rpc'],
  license='GPL',
  author='rdarder',
  author_email='darder@gmail.com',
  description='python rpc sample apps'
)

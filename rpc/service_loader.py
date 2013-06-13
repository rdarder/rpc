def setup_modules(module_names):
  """Service loader. Imports the modules given, runs setup_services on each
  of them and return a name to service mapping along with a list of filenames
   involved.
   :rtype: dict, list of str
  """
  services = {}
  filenames = []
  for module_name in module_names:
    module = __import__(module_name, fromlist=[module_name])
    filenames.append(module.__file__)
    mod_services = module.setup_services()
    services.update(mod_services)
  return services, filenames


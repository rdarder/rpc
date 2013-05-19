def setup_modules(module_names):
  services = {}
  filenames = []
  for module_name in module_names:
    module = __import__(module_name, fromlist=[module_name])
    filenames.append(module.__file__)
    mod_services = module.setup_services()
    services.update(mod_services)
  return services, filenames


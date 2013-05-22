import json
import types


class RegistryJsonEncoder(json.JSONEncoder):
  """ Simple JSON encoder that allows the service developer to add custom
  encoder for non basic types (i.e. other than list, dict, tuple, int, str,
  float, bool, etc
  ."""
  type_encoders = {}

  def default(self, obj):
    for obj_type in type(obj).mro():
      if obj_type in self.type_encoders:
        return self.type_encoders[obj_type](obj)
    return super(RegistryJsonEncoder, self).default(obj)


def encoder_for(src_type):
  """Decorator for registering new type encoders. The decorated function
  receives an object of the registered type (or a subtype of it) and returns
  another (simpler) object that can be json encoded.
  """

  def register_encoder(impl):
    RegistryJsonEncoder.type_encoders[src_type] = impl
    return impl

  return register_encoder


@encoder_for(types.GeneratorType)
def encode(gen):
  """Sample encoder for generators. We just convert a generator to a list,
  which is the encoder will then further process.
  """
  return list(gen)



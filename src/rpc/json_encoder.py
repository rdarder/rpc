import json
import types

class RegistryJsonEncoder(json.JSONEncoder):
  """ Quick and dirty json encoder which accepts functions as type based
  encoders.
  """
  type_encoders = {}

  def default(self, obj):
    for obj_type in type(obj).mro():
      if obj_type in self.type_encoders:
        return self.type_encoders[obj_type](obj)
    return super(RegistryJsonEncoder, self).default(obj)


def encoder_for(src_type):
  def register_encoder(impl):
    RegistryJsonEncoder.type_encoders[src_type] = impl
    return impl

  return register_encoder


@encoder_for(types.GeneratorType)
def encode(gen):
  return list(gen)



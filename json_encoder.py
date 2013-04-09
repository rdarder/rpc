import json
import types
from db import DBCursor


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

@encoder_for(DBCursor)
def encode(cursor):
  col_names = [desc[0] for desc in cursor.description]
  for row in cursor.fetchall():
    yield dict(zip(col_names, row))


@encoder_for(types.GeneratorType)
def encode(gen):
  return list(gen)



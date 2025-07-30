import sys,os,re,copy
from abc import ABC,abstractmethod

sys.path.append(re.sub('test.*','blues_lib',os.path.realpath(__file__)))
from model.decoder.SchemaValueReplacer import SchemaValueReplacer

class Model(ABC):
  def __init__(self,schema,materials):
    # { Schema } : the original schema, it wouldn't be changed
    self.__schema = schema
    # { List<dict> } : the business data rows
    self.__materials = materials if type(materials)==list else [materials]

    # {List<dict>} : the model list [{'schema':{},'material':{}}]
    self.__models = None

    # decode the schema, replace the schema's placeholders ${xxx} by material field values
    self.decode()
    
  def first(self):
    if not self.__models:
      return None
    return self.__models[0]

  def get(self):
    return self.__models

  def decode(self):
    '''
    Get the decoded schema list
    '''
    if not self.__schema or not self.__materials:
      return

    models = []
    for material in self.__materials:
      # use the schema's copy
      schema_copy = copy.deepcopy(self.__schema)
      self._decode_one(schema_copy,material)
      item = {
        'schema':schema_copy,
        'material':material
      }
      models.append(item)

    self.__models = models
  
  @abstractmethod
  def _decode_one(self,schema,material):
    pass

  

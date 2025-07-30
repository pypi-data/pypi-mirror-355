import sys,re,os,json
from jsonschema import validate
from jsonschema.exceptions import ValidationError
from abc import ABC,abstractmethod
sys.path.append(re.sub('blues_lib.*','blues_lib',os.path.realpath(__file__)))
from util.BluesLogger import BluesLogger 

class Schema(ABC):
  
  schemarule = None
  name = __name__

  def __init__(self):
    self._logger = BluesLogger.get_logger(self.name)

  @classmethod 
  def validate(cls,meta):
    try:
      validate(instance=meta, schema=cls.schemarule)
      return {
        "code":0,
        "message":"ok",
      }
    except ValidationError as e:
      return {
        "code":1,
        "message":e.message,
        "path":e.json_path,
      }
  

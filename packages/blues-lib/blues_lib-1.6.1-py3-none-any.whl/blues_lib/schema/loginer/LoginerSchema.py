import sys,os,re
from abc import ABC,abstractmethod
sys.path.append(re.sub('blues_lib.*','blues_lib',os.path.realpath(__file__)))
from schema.Schema import Schema     

class LoginerSchema(Schema,ABC):
  
  name = __name__

  def __init__(self,meta):

    self.browser = meta.get('browser')
    self.basic = meta.get('basic')
    self.proxy = meta.get('proxy')
    self.cookie = meta.get('cookie')

    # { ArrayAtom } : before fill
    self.preparation = meta.get('preparation')

    # { ArrayAtom } : fill and submit
    self.execution = meta.get('execution')

    # { ArrayAtom } : after submit
    self.cleanup = meta.get('cleanup')

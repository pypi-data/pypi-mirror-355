import sys,os,re
from abc import ABC,abstractmethod
sys.path.append(re.sub('blues_lib.*','blues_lib',os.path.realpath(__file__)))
from schema.Schema import Schema     

class PublisherSchema(Schema,ABC):

  name = __name__
  channel = 'publisher' 

  def __init__(self,meta={}):

    # {dict}
    self.browser = meta.get('browser')

    # {dict}
    self.basic = meta.get('basic')

    # {dict}
    self.limit = meta.get('limit')

    # {ArrayAtom}
    self.preparation = meta.get('preparation')

    # {ArrayAtom}
    self.preview_execution = meta.get('preview_execution')

    # {ArrayAtom}
    self.submit_execution = meta.get('submit_execution')

    # {ArrayAtom}
    self.cleanup = meta.get('cleanup')
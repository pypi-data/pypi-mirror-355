import sys,os,re
from abc import ABC
sys.path.append(re.sub('blues_lib.*','blues_lib',os.path.realpath(__file__)))
from schema.Schema import Schema     

class AISchema(Schema,ABC):

  name = __name__
  channel = 'ai' 

  def __init__(self,meta={}):

    # {dict}
    self.browser = meta.get('browser')

    # {dict}
    self.basic = meta.get('basic')

    # {dict}
    self.material = meta.get('material')

    # {ArrayAtom}
    self.preparation = meta.get('preparation')

    # {ArrayAtom}
    self.execution = meta.get('execution')

    # {ArrayAtom}
    self.cleanup = meta.get('cleanup')
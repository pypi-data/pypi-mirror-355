import sys,os,re
sys.path.append(re.sub('blues_lib.*','blues_lib',os.path.realpath(__file__)))
from schema.Schema import Schema     

class SpiderSchema(Schema):

  name = __name__
  type = 'spider' 
  
  def __init__(self,meta):

    # {dict}
    self.browser = meta.get('browser')

    # {dict}
    self.basic = meta.get('basic')

    # {dict}
    self.limit = meta.get('limit')

    # {ArrayAtom}
    self.brief_preparation = meta.get('brief_preparation')

    # {ArrayAtom}
    self.brief_execution = meta.get('brief_execution')

    # {ArrayAtom}
    self.brief_cleanup = meta.get('brief_cleanup')

    # {ArrayAtom}
    self.material_preparation = meta.get('material_preparation')

    # {ArrayAtom}
    self.material_execution = meta.get('material_execution')

    # {ArrayAtom}
    self.material_cleanup = meta.get('material_cleanup')
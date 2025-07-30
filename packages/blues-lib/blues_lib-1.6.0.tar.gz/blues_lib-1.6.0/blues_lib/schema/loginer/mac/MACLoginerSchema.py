import sys,os,re
from .schemarule import schemarule
sys.path.append(re.sub('blues_lib.*','blues_lib',os.path.realpath(__file__)))
from schema.loginer.LoginerSchema import LoginerSchema

class MACLoginerSchema(LoginerSchema):

  schemarule = schemarule
  name = __name__

  def __init__(self,meta):

    super().__init__(meta)

    # {dict<str,Atom>}
    self.verification = meta.get('verification')
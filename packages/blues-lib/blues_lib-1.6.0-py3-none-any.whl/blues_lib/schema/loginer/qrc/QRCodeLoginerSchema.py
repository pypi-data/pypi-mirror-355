import sys,os,re
from .schemarule import schemarule
sys.path.append(re.sub('blues_lib.*','blues_lib',os.path.realpath(__file__)))
from schema.loginer.LoginerSchema import LoginerSchema

class QRCodeLoginerSchema(LoginerSchema):

  schemarule = schemarule
  name = __name__

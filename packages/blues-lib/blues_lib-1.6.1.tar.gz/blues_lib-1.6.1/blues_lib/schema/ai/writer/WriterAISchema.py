import sys,os,re
from .schemarule import schemarule
sys.path.append(re.sub('blues_lib.*','blues_lib',os.path.realpath(__file__)))
from schema.ai.AISchema import AISchema

class WriterAISchema(AISchema):

  schemarule = schemarule
  name = __name__
  channel = 'writer' 

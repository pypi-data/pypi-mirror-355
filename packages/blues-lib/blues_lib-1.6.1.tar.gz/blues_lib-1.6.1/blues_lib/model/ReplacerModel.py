import sys,os,re
from .Model import Model
sys.path.append(re.sub('test.*','blues_lib',os.path.realpath(__file__)))
from model.decoder.SchemaValueReplacer import SchemaValueReplacer

class ReplacerModel(Model):
    
  def _decode_one(self,schema,material):
    # only replace the ${xxx} replaceholder
    request = {
      'schema':schema,
      'material':material, 
    }
    SchemaValueReplacer().handle(request)
  

import sys,os,re
sys.path.append(re.sub('blues_lib.*','blues_lib',os.path.realpath(__file__)))
from atom.AtomDictCreator import AtomDictCreator
from util.BluesLogger import BluesLogger 

class SchemaFactory():
  
  name = __name__

  def __init__(self,meta):
    self._meta = meta
    self._logger = BluesLogger.get_logger(self.name)
    
  def create(self, mode: str):
    # 构建方法名
    method_name = f"create_{mode.lower()}"
    
    # 检查方法是否存在
    if not hasattr(self, method_name):
      return None
        
    # 获取并调用方法
    method = getattr(self, method_name)
    return method()

  def _is_legal_meta(self,schema_class):
    result = schema_class.validate(self._meta)
    if result['code']==0:
      return True
    else:
      self._logger.error(f"The meta is illegal: {result['path']} {result['message']}")
    return False
  
  def _get_atom_meta(self):
    return AtomDictCreator.create(self._meta)
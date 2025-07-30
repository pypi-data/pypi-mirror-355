import sys,os,re
sys.path.append(re.sub('blues_lib.*','blues_lib',os.path.realpath(__file__)))
from sele.behavior.Behavior import Behavior
from sele.behavior.deco.BehaviorDeco import BehaviorDeco
from type.output.STDOut import STDOut

class Input(Behavior):
  
  @BehaviorDeco()
  def resolve(self):
    if self.kind!='input':
      return False 
    
    self.browser.element.input.write(self.selector,self.value,self.parent_selector,self.timeout)

    return STDOut()

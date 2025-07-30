import sys,os,re
sys.path.append(re.sub('blues_lib.*','blues_lib',os.path.realpath(__file__)))
from sele.behavior.Behavior import Behavior
from sele.behavior.deco.BehaviorDeco import BehaviorDeco
from type.output.STDOut import STDOut

class Select(Behavior):

  @BehaviorDeco()
  def resolve(self):
    if self.kind!='select':
      return False 
    
    self.browser.element.select.select_by_value_or_text(self.selector,self.value,self.parent_selector,self.timeout)

    return STDOut()


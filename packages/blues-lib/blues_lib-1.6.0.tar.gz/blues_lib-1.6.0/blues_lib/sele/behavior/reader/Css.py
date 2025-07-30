
import sys,os,re
sys.path.append(re.sub('blues_lib.*','blues_lib',os.path.realpath(__file__)))
from sele.behavior.Behavior import Behavior
from sele.behavior.deco.BehaviorDeco import BehaviorDeco
from type.output.STDOut import STDOut

class Css(Behavior):

  @BehaviorDeco()
  def resolve(self):
    if self.kind!='css':
      return False 
    
    # select one or multi checkboxs
    value = self.browser.element.info.get_css(self.selector,self.value,self.parent_selector,self.timeout)

    return STDOut(data=value)


import sys,os,re
sys.path.append(re.sub('blues_lib.*','blues_lib',os.path.realpath(__file__)))
from sele.behavior.Behavior import Behavior
from sele.behavior.deco.BehaviorDeco import BehaviorDeco
from type.output.STDOut import STDOut

class Choice(Behavior):

  @BehaviorDeco()
  def resolve(self):
    if self.kind!='choice':
      return False 
    
    # select one or multi checkboxs
    if self.value:
      self.browser.element.choice.select(self.selector,self.parent_selector,self.timeout)
    else:
      self.browser.element.choice.deselect(self.selector,self.parent_selector,self.timeout)

    return STDOut()


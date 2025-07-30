import sys,os,re
sys.path.append(re.sub('blues_lib.*','blues_lib',os.path.realpath(__file__)))
from sele.behavior.Behavior import Behavior
from sele.behavior.deco.BehaviorDeco import BehaviorDeco
from type.output.STDOut import STDOut

class TextArea(Behavior):

  @BehaviorDeco()
  def resolve(self):

    if self.kind!='textarea':
      return False 
   
    LF_count = self.atom.get_LF_count()
    self.browser.element.input.write_para(self.selector,self.value,LF_count,self.parent_selector,self.timeout)

    return STDOut()

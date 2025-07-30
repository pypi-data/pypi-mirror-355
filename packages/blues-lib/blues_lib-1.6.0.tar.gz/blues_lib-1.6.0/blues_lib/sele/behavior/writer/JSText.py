import sys,os,re,time
sys.path.append(re.sub('blues_lib.*','blues_lib',os.path.realpath(__file__)))
from sele.behavior.Behavior import Behavior
from sele.behavior.deco.BehaviorDeco import BehaviorDeco
from type.output.STDOut import STDOut

class JSText(Behavior):

  @BehaviorDeco()
  def resolve(self):

    if self.kind!='jstext':
      return False 
   
    # click to focus
    # value {str} : as setter
    # value {None} : as getter, return string
    value = self.browser.script.javascript.text(self.selector,self.value,self.parent_selector)
    return STDOut(data=value)

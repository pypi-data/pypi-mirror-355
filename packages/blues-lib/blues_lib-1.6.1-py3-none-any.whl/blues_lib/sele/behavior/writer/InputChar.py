import sys,os,re,time
sys.path.append(re.sub('blues_lib.*','blues_lib',os.path.realpath(__file__)))
from sele.behavior.Behavior import Behavior
from sele.behavior.deco.BehaviorDeco import BehaviorDeco
from type.output.STDOut import STDOut

class InputChar(Behavior):
  
  @BehaviorDeco()
  def resolve(self):
    if self.kind!='inputchar':
      return False 

    interval = self.atom.get_interval() 
    mode = self.atom.get_mode() 
    for char in self.value:
      time.sleep(interval)
      if mode=='replace':
        self.browser.element.input.write(self.selector,char,self.parent_selector,self.timeout)
      else:
        self.browser.element.input.append(self.selector,char,self.parent_selector,self.timeout)

    return STDOut()

import sys,os,re
sys.path.append(re.sub('blues_lib.*','blues_lib',os.path.realpath(__file__)))
from sele.behavior.Behavior import Behavior
from sele.behavior.deco.BehaviorDeco import BehaviorDeco
from type.output.STDOut import STDOut

class File(Behavior):

  @BehaviorDeco()
  def resolve(self):

    if self.kind!='file':
      return False 

    wait_time = self.atom.get_wait_time()
    self.browser.element.file.write(self.selector,self.value,wait_time,self.parent_selector,self.timeout)

    return STDOut()
  

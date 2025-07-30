import sys,os,re
sys.path.append(re.sub('blues_lib.*','blues_lib',os.path.realpath(__file__)))
from sele.behavior.Behavior import Behavior
from sele.behavior.deco.BehaviorDeco import BehaviorDeco
from type.output.STDOut import STDOut

class Hover(Behavior):

  @BehaviorDeco()
  def resolve(self):
    '''
    Just move the element into the window
    '''
    if self.kind!='hover':
      return False 
    
    self.browser.action.mouse.move_in(self.selector,self.parent_selector,self.timeout)
    return STDOut()

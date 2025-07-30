import sys,os,re
sys.path.append(re.sub('blues_lib.*','blues_lib',os.path.realpath(__file__)))
from sele.behavior.Behavior import Behavior
from sele.behavior.deco.BehaviorDeco import BehaviorDeco
from type.output.STDOut import STDOut

class Rollin(Behavior):

  @BehaviorDeco()
  def resolve(self):
    '''
    Just move the element into the window
    '''
    if self.kind!='rollin':
      return False 
    
    default_offset = {'x':0,'y':100}

    if not self.value:
      x = default_offset.get('x')
      y = default_offset.get('y')
    else:
      x = self.value.get('x')
      y = self.value.get('y')

    self.browser.action.wheel.scroll_from_element_to_offset(self.selector,x,y)
    return STDOut()

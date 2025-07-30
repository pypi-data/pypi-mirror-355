import sys,os,re
sys.path.append(re.sub('blues_lib.*','blues_lib',os.path.realpath(__file__)))
from sele.behavior.Behavior import Behavior
from sele.behavior.deco.BehaviorDeco import BehaviorDeco
from type.output.STDOut import STDOut

class Popup(Behavior):

  @BehaviorDeco()
  def resolve(self):
    '''
    Just move the element into the window
    '''
    if self.kind!='popup':
      return False 
    
    self.browser.element.popup.remove(self.selector)
    return STDOut()

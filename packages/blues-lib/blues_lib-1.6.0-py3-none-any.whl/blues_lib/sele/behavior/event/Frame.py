import sys,os,re
sys.path.append(re.sub('blues_lib.*','blues_lib',os.path.realpath(__file__)))
from sele.behavior.Behavior import Behavior
from sele.behavior.deco.BehaviorDeco import BehaviorDeco
from type.output.STDOut import STDOut

class Frame(Behavior):

  @BehaviorDeco()
  def resolve(self):
    '''
    Toggle the browser into the frame
    '''
    if self.kind!='frame':
      return False 
    
    if self.value=='in':
      self.browser.interactor.frame.switch_to(self.selector)
    else:
      self.browser.interactor.frame.switch_to_default()

    return STDOut()

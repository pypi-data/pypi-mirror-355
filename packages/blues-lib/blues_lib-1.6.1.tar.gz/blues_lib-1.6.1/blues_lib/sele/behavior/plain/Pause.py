import sys,os,re
sys.path.append(re.sub('blues_lib.*','blues_lib',os.path.realpath(__file__)))
from sele.behavior.Behavior import Behavior
from sele.behavior.deco.BehaviorDeco import BehaviorDeco
from util.BluesDateTime import BluesDateTime
from type.output.STDOut import STDOut

class Pause(Behavior):

  @BehaviorDeco()
  def resolve(self):
    '''
    Just move the element into the window
    '''
    if self.kind!='pause':
      return False 
    
    BluesDateTime.count_down({
      'duration':self.value,
      'title':self.title,
    })
    return STDOut()

import sys,os,re,time

sys.path.append(re.sub('blues_lib.*','blues_lib',os.path.realpath(__file__)))
from atom.composite.MapAtom import MapAtom
from sele.behavior.Behavior import Behavior
from type.output.STDOut import STDOut

from sele.behavior.MicroBehaviorChain import MicroBehaviorChain  

# decorator
from sele.behavior.deco.BehaviorDeco import BehaviorDeco

class Map(Behavior):

  @BehaviorDeco(False,True)
  def resolve(self):
    '''
    It's a Behavior subclass
    It deal a atom dict
    '''
    if self.kind!='map':
      return False 
    
    pause = self.atom.get_pause()
    if type(self.value)==dict:

      cal_dict = {}
      for atom in self.value.values():
        # support MapAtom nest
        if type(atom) == MapAtom:
          handler = Map(self.browser,atom)
        else:
          handler = MicroBehaviorChain(self.browser,atom)

        title = atom.get_title()
        value = handler.handle()

        if value:
          cal_dict[title] = value.data
        else:
          cal_dict[title] = None

        time.sleep(pause)

    return STDOut(data=cal_dict)


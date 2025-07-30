import sys,os,re,copy

sys.path.append(re.sub('blues_lib.*','blues_lib',os.path.realpath(__file__)))

from sele.behavior.Behavior import Behavior
from atom.composite.ArrayAtom import ArrayAtom
from type.output.STDOut import STDOut

# only need Array
from sele.behavior.MicroBehaviorChain import MicroBehaviorChain  
from sele.behavior.spider.Brief import Brief  
from sele.behavior.spider.Para import Para  

# decorator
from sele.behavior.deco.BehaviorDeco import BehaviorDeco

class News(Behavior):

  @BehaviorDeco(False,True)
  def resolve(self):
    '''
    It's a Behavior subclass
    It deal a atom list
    '''
    if self.kind!='news':
      return False 
  
    if type(self.value)!=list and type(self.value)!=tuple:
      return STDOut(501,'value type is not list or tuple')
    
    field_dict = {}
    for atom in self.value:
      if atom.get_kind()=='brief':
        handler = Brief(self.browser,atom)
      else:
        # set the parent selector
        if self.selector:
          copy_of_atom = self.__get_copy_of_atom(atom,self.selector)
          handler = MicroBehaviorChain(self.browser,copy_of_atom)
        else:
          handler = MicroBehaviorChain(self.browser,atom)
      
      outcome = handler.handle()
      if outcome and outcome.data:
        key = atom.get_title()
        field_dict[key] = outcome.data

    return STDOut(data=field_dict)


  def __get_copy_of_atom(self,atom,unit_element):
    '''
    Add the unit container' selector as the reader atom's parent selector
    '''
    copy_of_atom = copy.deepcopy(atom)
    # set a selector firstly
    if copy_of_atom.get_selector():
      copy_of_atom.set_parent_selector(unit_element)
    else:
      copy_of_atom.set_selector(unit_element)

    return copy_of_atom


import sys,os,re,copy

sys.path.append(re.sub('blues_lib.*','blues_lib',os.path.realpath(__file__)))

from sele.behavior.Behavior import Behavior
from atom.composite.ArrayAtom import ArrayAtom
from type.output.STDOut import STDOut

# only need Array
from sele.behavior.composite.Array import Array  

# decorator
from sele.behavior.deco.BehaviorDeco import BehaviorDeco

class Brief(Behavior):

  @BehaviorDeco(False,True)
  def resolve(self):
    '''
    It's a Behavior subclass
    It deal a atom list
    '''
    if self.kind!='brief':
      return False 
    
    # get data unit's parent selector
    if not self.selector:
      return STDOut(501,'selector is missing')
  
    if type(self.value)!=list and type(self.value)!=tuple:
      return STDOut(502,'value type is not list or tuple')
    
    # query_all unit elements
    unit_elements = self.browser.waiter.querier.query_all(self.selector)
    if not unit_elements:
      return STDOut(503,'selector (%s) element is missing' % self.selector)
    
    # Iterate over the data unit to get the row data
    rows = []
    for unit_element in unit_elements:
      atoms_copy = self.__get_atoms_copy(self.value,unit_element)
      # replace the atom's select to current unit's web_element
      array_atom = ArrayAtom('array atom',atoms_copy)
      handler = Array(self.browser,array_atom)
      outcome = handler.handle()
      if outcome and outcome.data:
        rows.append(outcome.data)

    return STDOut(data=rows)


  def __get_atoms_copy(self,atoms,unit_element):
    '''
    Add the unit container' selector as the reader atom's parent selector
    '''
    atoms_copy = copy.deepcopy(atoms)
    for atom in atoms_copy:
      # set a selector firstly
      if atom.get_selector():
        atom.set_parent_selector(unit_element)
      else:
        atom.set_selector(unit_element)

    return atoms_copy


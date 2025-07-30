import sys,os,re,copy

sys.path.append(re.sub('blues_lib.*','blues_lib',os.path.realpath(__file__)))
from atom.composite.ArrayAtom import ArrayAtom
from atom.composite.MapAtom import MapAtom
from sele.behavior.composite.Array import Array
from sele.behavior.composite.Map import Map
from sele.behavior.Behavior import Behavior
from type.output.STDOut import STDOut

# reader
from sele.behavior.MicroBehaviorChain import MicroBehaviorChain  

# decorator
from sele.behavior.deco.BehaviorDeco import BehaviorDeco

class ImageText(Behavior):

  @BehaviorDeco(False,True)
  def resolve(self):
    '''
    It's a Behavior subclass
    It deal a atom list
    '''
    if self.kind!='imagetext':
      return False 

    if not self.value:
      return False 

    if not self.value.get('data') or not self.value.get('image') or not self.value.get('text'):
      return False 
    
    rows = self.value.get('data').get_value()
    ori_image_atom = self.value.get('image')
    ori_text_atom = self.value.get('text')
    
    if not type(rows)==list and not type(rows)==tuple:
      return False

    for row in rows:

      # using the copy to avoid the placehoder is replaced 
      text_atom = copy.deepcopy(ori_text_atom)
      image_atom = copy.deepcopy(ori_image_atom)
      # replace the real data before handled

      if row.get('text'):
        self._replace(row,text_atom) 
        if type(text_atom) == ArrayAtom:
          text_handler = Array(self.browser,text_atom)
        elif type(text_atom) == MapAtom:
          text_handler = Map(self.browser,text_atom)
        else:
          text_handler = MicroBehaviorChain(self.browser,text_atom)
        text_handler.handle()

      if row.get('image'):
        self._replace(row,image_atom) 
        if type(image_atom) == ArrayAtom:
          text_handler = Array(self.browser,image_atom)
        elif type(image_atom) == MapAtom:
          text_handler = Map(self.browser,image_atom)
        else:
          text_handler = MicroBehaviorChain(self.browser,image_atom)
        text_handler.handle()

    return STDOut(data=rows)
  
  def _replace(self,item,atom):
    atom_value = atom.get_value()
    if type(atom) == ArrayAtom:
      for child_atom in atom_value:
        self._replace_one(item,child_atom)
    elif type(atom) == MapAtom:
      for key in atom_value:
        self._replace_one(item,atom_value[key])
    else:
      self._replace_one(item,atom)
    
  
  def _replace_one(self,item,atom):
    '''
    Replace the placehoders in the atom
    {Dict} item : the data dict
    {Atom} atom : a base atom
    '''
    atom_value = atom.get_value()
    if not type(atom_value)==str or not re.search(r'^\$\{.+\}$',atom_value):
      return
    
    for key in item:
      pattern = r'^\$\{'+key+r'\}$'
      if not re.search(pattern,atom_value):
        continue

      value = item.get(key)
      atom.set_value(value)
      break
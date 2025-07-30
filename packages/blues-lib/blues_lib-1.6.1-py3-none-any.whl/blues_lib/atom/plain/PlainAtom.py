from abc import ABC
import sys,os,re

sys.path.append(re.sub('blues_lib.*','blues_lib',os.path.realpath(__file__)))
from atom.Atom import Atom     

class PlainAtom(Atom,ABC):

  _category = 'plain'
  
  def __init__(self,kind,title,value):
    '''
    Create a plain atom instance
      This kind of atom has no selector, but must has a value
    Parameter:
      kind (str) : the atom's kind
      title (str) : the atom's title
      value (str) : the atom's value
    Returns:
      Atom : a atom instance
    '''
    super().__init__(self._category,kind,title)
    self._value = value
  
  # getter
  def get_value(self):
    return self._value
  
  # setter
  def set_value(self,value):
    self._value = value


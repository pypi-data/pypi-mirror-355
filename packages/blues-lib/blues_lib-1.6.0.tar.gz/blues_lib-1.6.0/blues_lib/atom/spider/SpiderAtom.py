from abc import ABC
import sys,os,re

sys.path.append(re.sub('blues_lib.*','blues_lib',os.path.realpath(__file__)))
from atom.Atom import Atom     

class SpiderAtom(Atom,ABC):

  _category = 'spider'

  def __init__(self,kind,title,selector='',value=None):
    '''
    A atoms' collections ,don't case the item atom's kind
    Parameter:
      title (str) : the atom's title
      selector (str) : the atoms' parent selector
      value (ArrayAtom) : the atom's title will be the return dict's key
    Returns:
      BluesAtom : a atom instance
    '''
    super().__init__(self._category,kind,title)
    self._selector = selector
    self._value = value
  
  # getter
  def get_selector(self):
    return self._selector
  
  def get_value(self):
    return self._value
  
  # setter
  def set_selector(self,selector):
    self._selector = selector

  def set_value(self,value):
    self._value = value





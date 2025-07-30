from abc import ABC
import sys,os,re

sys.path.append(re.sub('blues_lib.*','blues_lib',os.path.realpath(__file__)))
from atom.Atom import Atom     

class ReaderAtom(Atom,ABC):

  _category = 'reader'
  
  def __init__(self,kind,title,selector,value=None,parent_selector=None,timeout=10,selector_template=''):
    '''
    A readable elment 
    Parameter:
      kind (str) : the atom's kind
      title (str) : the atom's description
      selector (str|list) : the element's css selector
      value (str) : the value's meaning base on the concrete atom
      parent_selector (str) : the atom's parent selector
      timeout (int) : the Quieier.query's wait timeout time
      selector_template (str) : the atom's selector tempalte, with placeholder ${}
    Returns:
      BluesAtom : a atom instance
    '''
    super().__init__(self._category,kind,title)
    self._selector = selector
    self._value = value
    self._parent_selector = parent_selector
    self._timeout = timeout
    self._selector_template = selector_template

  # getter
  def get_selector(self):
    return self._selector
  
  def get_selector_template(self):
    return self._selector_template
  
  def get_value(self):
    return self._value
  
  def get_parent_selector(self):
    return self._parent_selector
  
  def get_timeout(self):
    return self._timeout
  
  # setter
  def set_selector(self,selector):
    self._selector = selector

  def set_selector_template(self,selector_template):
    self._selector_template = selector_template

  def set_value(self,value):
    self._value = value

  def set_parent_selector(self,parent_selector):
    self._parent_selector = parent_selector

  def set_timeout(self,timeout):
    self._timeout = timeout


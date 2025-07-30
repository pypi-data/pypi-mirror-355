from abc import ABC

class Atom(ABC):
  
  def __init__(self,category,kind,title):
    '''
    Create a atom instance
    Parameter:
      kind {str} : the atom's kind, can't be changed
      title {str} : the atom's title
    Return:
      Atom : a atom instance
    '''
    self._category = category
    self._kind = kind
    self._title = title 
  
  # getter
  def get_category(self):
    return self._category
  
  def get_kind(self):
    return self._kind
  
  def get_title(self):
    return self._title
  
  # setter
  def set_title(self,title):
    self._title = title


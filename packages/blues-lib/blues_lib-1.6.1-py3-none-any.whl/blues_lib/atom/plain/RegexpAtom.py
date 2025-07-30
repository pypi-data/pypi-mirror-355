
from .PlainAtom import PlainAtom

class RegexpAtom(PlainAtom):

  _kind = 'regexp' 

  def __init__(self,title,value):
    '''
    Create a plain Atom that has a regexp pattern value
    Parameter:
      title (str) : the atom's title
      value (str) : the value: a regexp string
    Returns:
      PlainAtom : a atom instance
    '''
    super().__init__(self._kind,title,value)


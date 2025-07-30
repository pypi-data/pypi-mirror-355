from .PlainAtom import PlainAtom

class DataAtom(PlainAtom):

  _kind = 'data' 

  def __init__(self,title,value):
    '''
    Create a plain Atom that has a any type value
    It's a general value Atom
    Parameter:
      title (str) : the atom's description
      value (any) : the value
    Returns:
      PlainAtom : a atom instance
    '''
    super().__init__(self._kind,title,value)


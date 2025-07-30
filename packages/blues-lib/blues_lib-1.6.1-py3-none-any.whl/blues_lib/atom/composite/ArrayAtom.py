from .CompositeAtom import CompositeAtom

class ArrayAtom(CompositeAtom):

  _kind = 'array' 

  def __init__(self,title,value=None,pause=0):
    '''
    A comon atom list
    Parameter:
      title (str) : the atom's description
      selector (str) : the child atom's parent selector
      value (list<Atom>) : must be the atom list
    Returns:
      BluesAtom : a atom instance
    '''
    super().__init__(self._kind,title,value,pause)


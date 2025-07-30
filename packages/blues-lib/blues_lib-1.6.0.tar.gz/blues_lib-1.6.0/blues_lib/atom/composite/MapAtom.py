from .CompositeAtom import CompositeAtom

class MapAtom(CompositeAtom):

  _kind = 'map' 

  def __init__(self,title,value=None,pause=0):
    '''
    A comon atom list
    Parameter:
      title (str) : the atom's description
      selector (str) : the child atom's parent selector
      value (dict<str,Atom>) : the atom dict
    Returns:
      BluesAtom : a atom instance
    '''
    super().__init__(self._kind,title,value,pause)


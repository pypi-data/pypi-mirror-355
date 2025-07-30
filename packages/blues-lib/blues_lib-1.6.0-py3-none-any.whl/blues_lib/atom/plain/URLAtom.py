from .PlainAtom import PlainAtom

class URLAtom(PlainAtom):
    
  _kind = 'url'

  def __init__(self,title,value):
    '''
    Create a plain Atom that has a url value
    Parameter:
      title (str) : the atom's description
      value (str) : the url
    Returns:
      PlainAtom : a atom instance
    '''
    super().__init__(self._kind,title,value)


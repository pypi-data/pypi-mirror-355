from .ReaderAtom import ReaderAtom

class ShotAtom(ReaderAtom):

  _kind = 'shot' 

  def __init__(self,title,selector=None,value=None,parent_selector=None,timeout=10,selector_template=''):
    '''
    A common element
    Parameter:
      title (str) : the atom's description
      selector (str|None) : the element css selector, if is None shot the window
      value (str|None) : the local file path to save the image
    Returns:
      BluesAtom : a atom instance
    '''
    super().__init__(self._kind,title,selector,value,parent_selector,timeout,selector_template)


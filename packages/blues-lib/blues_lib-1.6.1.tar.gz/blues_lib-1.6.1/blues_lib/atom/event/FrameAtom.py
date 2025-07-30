from .EventAtom import EventAtom

class FrameAtom(EventAtom):
    
  kind = 'frame'

  def __init__(self,title,selector,value=None,parent_selector=None,timeout=10,selector_template=''):
    '''
    A iframe element atom
    Parameter:
      title (str) : the atom's title
      selector (str) : the element's css selector
      value (str) : the status to frame, 'in' | 'out'
    Returns:
      Atom : a atom instance
    '''
    super().__init__(self.kind,title,selector,value,parent_selector,timeout,selector_template)



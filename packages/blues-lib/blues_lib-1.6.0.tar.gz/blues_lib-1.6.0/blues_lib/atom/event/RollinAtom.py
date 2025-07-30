from .EventAtom import EventAtom

class RollinAtom(EventAtom):
    
  kind = 'rollin'

  def __init__(self,title,selector,value=None,parent_selector=None,timeout=10,selector_template=''):
    '''
    A element atom, the acter will move the element in the window
    Parameter:
      title (str) : the atom's title
      selector (str) : the element's css selector
      value (dict) : the offset by the aim element {'x':0,'y':100}
    Returns:
      Atom : a atom instance
    '''
    super().__init__(self.kind,title,selector,value,parent_selector,timeout,selector_template)



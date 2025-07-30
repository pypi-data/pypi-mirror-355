from .EventAtom import EventAtom

class PopupAtom(EventAtom):
    
  kind = 'popup'

  def __init__(self,title,selector,value=None,parent_selector=None,timeout=10,selector_template=''):
    '''
    A element atom, the acter will move the element in the window
    Parameter:
      title (str) : the atom's title
      selector (str|list) : one or multi element's css selector
      value (None) : the optional value, base on the atom's kind
    Returns:
      Atom : a atom instance
    '''
    super().__init__(self.kind,title,selector,value,parent_selector,timeout,selector_template)



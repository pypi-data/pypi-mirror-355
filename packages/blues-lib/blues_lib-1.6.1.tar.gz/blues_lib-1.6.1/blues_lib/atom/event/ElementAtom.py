from .EventAtom import EventAtom

class ElementAtom(EventAtom):
    
  kind = 'element'

  def __init__(self,title,selector,value=None,parent_selector=None,timeout=10,selector_template=''):
    '''
    A element atom, it's a common atom
    Parameter:
      title (str) : the atom's title
      selector (str) : the element's css selector
      value (any) : the optional value, base on the atom's kind
    Returns:
      Atom : a atom instance
    '''
    super().__init__(self.kind,title,selector,value,parent_selector,timeout,selector_template)



from .WriterAtom import WriterAtom

class JSCssAtom(WriterAtom):

  _kind = 'jscss' 

  def __init__(self,title,selector,value=None,parent_selector=None,timeout=10,selector_template=''):
    '''
    A multi lines input type element
    Parameter:
      title (str) : the atom's description
      selector (str) : the textarea's css selector
      value (dict) : 
        - None : getter
        - str : setter

    Returns:
      BluesAtom : a atom instance
    '''
    super().__init__(self._kind,title,selector,value,parent_selector,timeout,selector_template)

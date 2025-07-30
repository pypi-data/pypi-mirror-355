from .WriterAtom import WriterAtom

class InputAtom(WriterAtom):

  _kind = 'input' 

  def __init__(self,title,selector,value='',parent_selector=None,timeout=10,selector_template=''):
    '''
    A single line input type element
    Parameter:
      title (str) : the atom's description
      selector (str) : the text input's css selector
      value (str) : the input value
    Returns:
      BluesAtom : a atom instance
    '''
    super().__init__(self._kind,title,selector,value,parent_selector,timeout,selector_template)


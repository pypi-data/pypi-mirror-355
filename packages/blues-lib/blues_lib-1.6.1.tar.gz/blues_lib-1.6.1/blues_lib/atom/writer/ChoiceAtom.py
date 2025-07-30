from .WriterAtom import WriterAtom

class ChoiceAtom(WriterAtom):

  _kind = 'choice' 

  def __init__(self,title,selector,value,parent_selector=None,timeout=10,selector_template=''):
    '''
    Create a checkbox atom instance
    Select one or more values
    Parameter:
      title (str) : the atom's title
      selector (str|list) : ore or more selector
      value (bool) : the selector's selected status
    Returns:
      BluesAtom : a atom instance
    '''
    super().__init__(self._kind,title,selector,value,parent_selector,timeout,selector_template)




from .SpiderAtom import SpiderAtom

class ParaAtom(SpiderAtom):

  _kind = 'para' 

  def __init__(self,title,selector,value):
    '''
    A special atom for paragraphs, it's value has a specific structure
    Parameter:
      title (str) : the atom's description
      selector (str) : the data parent selector
      value (list<atom>) : the filed reader atom, the atom's title will be the return dict's key
   Returns:
      BluesAtom : a atom instance
    '''
    super().__init__(self._kind,title,selector,value)

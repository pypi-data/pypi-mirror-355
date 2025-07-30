from .SpiderAtom import SpiderAtom

class BriefAtom(SpiderAtom):

  _kind = 'brief' 

  def __init__(self,title,selector,value):
    '''
    A special common brief, it's value has a specific structure
    Parameter:
      title (str) : the atom's description
      selector (str) : the data unit selector
      value (list<atom>) : the filed reader atom, the atom's title will be the return dict's key
    Returns:
      BluesAtom : a atom instance
    '''
    super().__init__(self._kind,title,selector,value)


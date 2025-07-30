from .ReleaserAtom import ReleaserAtom

class ImageTextAtom(ReleaserAtom):

  _kind = 'imagetext' 

  def __init__(self,title,selector='',value=None):
    '''
    A comon atom list
    Parameter:
      title (str) : the atom's description
      selector (str) : the child atom's parent selector
      value (dict) : a structure dict
        - {DataAtom} data - list<dict> : the data rows
        - {ArrayAtom|MapAtom} atom : the execution atoms
    Returns:
      BluesAtom : a atom instance
    '''
    super().__init__(self._kind,title,selector,value)


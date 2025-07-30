from .WriterAtom import WriterAtom

class InputCharAtom(WriterAtom):

  _kind = 'inputchar' 

  def __init__(self,title,selector,value='',interval=1,mode='append',parent_selector=None,timeout=10,selector_template=''):
    '''
    Iput char one by one
    Parameter:
      title (str) : the atom's description
      selector (str) : the text input's css selector
      value (str) : the input value
      interval (int) : the interval seconds
      mode (str) : the input mode 'replace' or 'append'
    Returns:
      BluesAtom : a atom instance
    '''
    super().__init__(self._kind,title,selector,value,parent_selector,timeout,selector_template)
    self._interval = interval
    self._mode = mode

  # getter
  def get_interval(self):
    return self._interval
  
  def get_mode(self):
    return self._mode
  
  # setter
  def set_interval(self,interval):
    self._interval = interval

  def set_mode(self,mode):
    self._mode = mode


from .WriterAtom import WriterAtom

class FileAtom(WriterAtom):

  _kind = 'file' 

  def __init__(self,title,selector,value,wait_time=5,parent_selector=None,timeout=10,selector_template=''):
    '''
    A file type input element
    Parameter:
      title (str) : the atom's description
      selector (str) : the text input's css selector
      value (str|list) : the file or file list
      wait_time (int) : the file uploading wait time
      parent_selector (str) : the atom's parent selector
      timeout (int) : the Quieier.query's wait timeout time
    Returns:
      BluesAtom : a atom instance
    '''
    super().__init__(self._kind,title,selector,value,parent_selector,timeout,selector_template)
    self._wait_time = wait_time

  # getter
  def get_wait_time(self):
    return self._wait_time
  
  # setter
  def set_wait_time(self,wait_time):
    self._wait_time = wait_time
 

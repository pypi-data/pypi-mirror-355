from .WriterAtom import WriterAtom

class TextAreaAtom(WriterAtom):

  _kind = 'textarea' 

  def __init__(self,title,selector,value,LF_count=1,parent_selector=None,timeout=10,selector_template=''):
    '''
    A multi lines input type element
    Parameter:
      title (str) : the atom's description
      selector (str) : the textarea's css selector
      value (str|list<str>) : one or multi text lines, the list's element is a simple string
        - str : single line text
        - list<str> : multi lines text, will add eol after every line
      eol (int) : the end-of-line count after a line, the default value is 1

    Returns:
      BluesAtom : a atom instance
    '''
    super().__init__(self._kind,title,selector,value,parent_selector,timeout,selector_template)
    self._LF_count = LF_count

  # getter
  def get_LF_count(self):
    return self._LF_count
  
  # setter
  def set_LF_count(self,LF_count):
    self._LF_count = LF_count

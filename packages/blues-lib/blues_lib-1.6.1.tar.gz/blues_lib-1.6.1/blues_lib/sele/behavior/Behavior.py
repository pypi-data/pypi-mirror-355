import sys,os,re
from abc import ABC,abstractmethod
sys.path.append(re.sub('blues_lib.*','blues_lib',os.path.realpath(__file__)))
from type.output.STDOut import STDOut

class Behavior(ABC):

  def __init__(self,browser,atom):
    '''
    The abstract class of handlers 
    Parameter:
      browser {Browser} : the browser instance, the real implementer
      atom {Atom} 
    '''
    self.browser = browser
    self.atom = atom
    self.title = self.atom.get_title()
    self.category = self.atom.get_category()
    self.kind = self.atom.get_kind()
    # Acter can't support the plain atoms
    if hasattr(self.atom,'get_selector'):
      self.selector = self.atom.get_selector()
    else:
      self.selector = None

    if hasattr(self.atom,'get_parent_selector'):
      self.parent_selector = self.atom.get_parent_selector()
    else:
      self.parent_selector = None

    if hasattr(self.atom,'get_value'):
      self.value = self.atom.get_value()
    else:
      self.value = None

    if hasattr(self.atom,'get_timeout'):
      self.timeout = self.atom.get_timeout()
    else:
      self.timeout = None

    self.next_handler = None
  
  def set_next(self,handler):
    '''
    Set the next handler
    Parameter:
      handler {Acter} : the next handler
    Returns 
      {Acter} : return the passin Acter
    '''
    self.next_handler = handler
    return handler

  def handle(self):
    '''
    Write the field by a handler in the chain
    '''
    outcome = self.resolve()
    if isinstance(outcome,STDOut):
      return outcome
    elif self.next_handler:
      return self.next_handler.handle()
    else:
      return False

  @abstractmethod
  def resolve(self):
    '''
    This method will be implemented by subclasses
    Returns:
      {False} : the handler can't deal with the Atom
      {STDOut} : the result of handling
    '''
    pass


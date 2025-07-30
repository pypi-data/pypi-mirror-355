import sys,os,re
from abc import ABC,abstractmethod
sys.path.append(re.sub('blues_lib.*','blues_lib',os.path.realpath(__file__)))
from atom.Atom import Atom

class DecoderHandler(ABC):

  def __init__(self):
    '''
    The abstract class of handlers 
    '''
    self._next_handler = None
  
  def set_next(self,handler):
    '''
    Set the next handler
    Parameter:
      handler {Acter} : the next handler
    Returns 
      {Acter} : return the passin Acter
    '''
    self._next_handler = handler
    return handler
  

  def handle(self,request):
    '''
    Parameters:
      request {dict} 
        - schema {Schema}
        - material {dict}
    '''
    result = self.resolve(request)
    if self._next_handler:
      return self._next_handler.handle(request)
    else:
      return result

  @abstractmethod
  def resolve(self,data):
    '''
    This method will be implemented by subclasses
    '''
    pass

  def _get_decode_atoms(self,schema):
    '''
    Get the schema's all Atom fields
    Returns 
      {list<Atom>} : change the atom's value and selector directly
    '''
    keys = schema.__dict__
    atoms = []
    for key in keys:
      value = getattr(schema,key)
      if isinstance(value,Atom):
        atoms.append(value)
    return atoms

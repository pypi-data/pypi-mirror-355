import sys,os,re
from abc import ABC,abstractmethod
sys.path.append(re.sub('blues_lib.*','blues_lib',os.path.realpath(__file__)))
from util.BluesLogger import BluesLogger 

class CrawlerHandler(ABC):

  name = __name__

  def __init__(self):
    '''
    The abstract class of handlers 
    '''
    self.message = '' # log info
    self._next_handler = None
    # {logger}
    self._logger = BluesLogger.get_logger(self.name)
    
  def set_next(self,handler):
    '''
    Set the next handler
    Parameter:
      handler {ReaderHandler} : the next handler
    Returns 
      {ReaderHandler}  
    '''
    self._next_handler = handler
    return handler
  

  def handle(self,request):
    '''
    Parameters:
      request {dict} 
        - schema {Schema}
        - count {int} : the count of got materials
        - briefs {List<Brief>} : first input is None
        - materials {List<Material>} : first input is None
    Returns:
      {None} : update the rquest directily
    '''
    self.resolve(request)
    if self._next_handler:
      self._next_handler.handle(request)

  @abstractmethod
  def resolve(self,request):
    '''
    This method will be implemented by subclasses
    '''
    pass


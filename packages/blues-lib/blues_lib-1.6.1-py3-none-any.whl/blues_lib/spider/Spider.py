import sys,re,os
from abc import ABC,abstractmethod
sys.path.append(re.sub('blues_lib.*','blues_lib',os.path.realpath(__file__)))
from util.BluesLogger import BluesLogger 
from deco.LogDeco import LogDeco

class Spider(ABC):

  def __init__(self,request):
    '''
    @param {Browser} browser
    @param {SpiderSchema} schema
    '''
    self.request = request
    self._logger = BluesLogger.get_logger(__name__)
    self.message = ''

  @LogDeco()
  def spide(self):
    crawl_chain = self.get_chain()
    crawl_chain.handle(self.request)
    self.request['browser'].quit()
    self.message = self.get_message()
    return self.get_items()

  @abstractmethod
  def get_chain(self):
    '''
    Template method: get the crawl chain
    '''
    pass

  @abstractmethod
  def get_items(self):
    '''
    Template method: get the return value from the request
    '''
    pass
  
  @abstractmethod
  def get_message(self):
    '''
    Template method: get the log message
    '''
    pass
  


    
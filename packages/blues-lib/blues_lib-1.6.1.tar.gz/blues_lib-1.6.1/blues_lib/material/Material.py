from abc import ABC,abstractmethod

class Material(ABC):

  @abstractmethod
  def get(self,query_condition):
    '''
    Return all query_condition rows
    Parameters:
      query_condition {dict} 
    Returns {list<dict>}
    '''
    pass
  
  @abstractmethod
  def first(self):
    '''
    Return the first query_condition rows
    Returns {dict}
    '''
    pass


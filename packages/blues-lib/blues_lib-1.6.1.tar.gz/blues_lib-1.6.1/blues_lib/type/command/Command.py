from abc import ABC,abstractmethod

class Command(ABC):

  name = __name__
  
  def __init__(self,context):
    self._context = context

  @abstractmethod  
  def execute(self):
    pass


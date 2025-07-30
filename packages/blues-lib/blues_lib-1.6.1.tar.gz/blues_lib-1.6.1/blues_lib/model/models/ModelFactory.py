from abc import ABC,abstractmethod

class ModelFactory(ABC):

  def create(self,expected_channel_ratio,query_query_condition):
    pass

  def create_events(self,query_condition):
    pass

  def create_news(self,query_condition):
    pass
    
  def create_gallery(self,query_condition):
    pass

  def create_video(self,query_condition):
    pass

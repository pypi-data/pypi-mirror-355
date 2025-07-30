import sys,os,re
from .schemarule import schemarule
sys.path.append(re.sub('blues_lib.*','blues_lib',os.path.realpath(__file__)))
from schema.publisher.PublisherSchema import PublisherSchema

class ArticlePublisherSchema(PublisherSchema):

  schemarule = schemarule
  name = __name__
  channel = 'article' 

  def __init__(self,meta):
    
    super().__init__(meta)

    # {ArrayAtom}
    self.title_execution = meta.get('title_execution')

    # {ArrayAtom}
    self.others_execution = meta.get('others_execution')

    # {ArrayAtom}
    self.thumbnail_execution = meta.get('thumbnail_execution')

    # {ArrayAtom}
    self.content_preparation = meta.get('content_preparation')

    # {ArrayAtom}
    self.content_execution = meta.get('content_execution')

    # {ArrayAtom}
    self.content_cleanup = meta.get('content_cleanup')
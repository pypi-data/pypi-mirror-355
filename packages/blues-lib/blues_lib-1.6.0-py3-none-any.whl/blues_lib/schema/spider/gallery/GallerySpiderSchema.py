import sys,os,re
from .schemarule import schemarule
sys.path.append(re.sub('blues_lib.*','blues_lib',os.path.realpath(__file__)))
from schema.spider.SpiderSchema import SpiderSchema

class GallerySpiderSchema(SpiderSchema):

  schemarule = schemarule
  name = __name__
  type = 'gallery' 

  def __init__(self,meta={}):

    super().__init__(meta)

    self.max_image_size = meta.get('max_image_size',30)

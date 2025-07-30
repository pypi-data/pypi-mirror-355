import sys,os,re
from .schemarule import schemarule
sys.path.append(re.sub('blues_lib.*','blues_lib',os.path.realpath(__file__)))
from schema.spider.SpiderSchema import SpiderSchema

class ArticleSpiderSchema(SpiderSchema):

  schemarule = schemarule
  name = __name__
  type = 'article'

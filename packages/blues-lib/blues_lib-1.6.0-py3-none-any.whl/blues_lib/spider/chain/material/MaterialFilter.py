import sys,os,re
sys.path.append(re.sub('blues_lib.*','blues_lib',os.path.realpath(__file__)))
from deco.LogDeco import LogDeco
from spider.chain.CrawlerHandler import CrawlerHandler
from pool.BluesMaterialIO import BluesMaterialIO  

class MaterialFilter(CrawlerHandler):
  '''
  Remove the unavailable breifs
  '''
  @LogDeco()
  def resolve(self,request):
    if not request or not request.get('material'):
      self.__set_message('The param request.material is empty')
      return
    
    self.__filter(request)

  def __set_message(self,message):
    self.message = message

  def __filter(self,request):
    material = request.get('material')
    message = 'Filter: the material is legal'
    if not BluesMaterialIO.is_legal_material(material):
      message = 'Filter: the material is illegal'
      request['material'] = None

    elif not self.__is_limit_valid(request):
      message = 'Filter: the material is illegal: illegal text length'
      request['material'] = None
    
    self.__set_message(message)

  def __is_limit_valid(self,request):
    schema = request.get('schema')
    material = request.get('material')
    min_content_length = schema.limit.get('min_content_length')
    max_content_length = schema.limit.get('max_content_length')

    text_len = len(material.get('material_body_text',''))

    if text_len < min_content_length or text_len > max_content_length:
      return False
    else:
      return True



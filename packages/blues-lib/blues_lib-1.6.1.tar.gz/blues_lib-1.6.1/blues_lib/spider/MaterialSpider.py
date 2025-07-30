import sys,re,os,json
sys.path.append(re.sub('blues_lib.*','blues_lib',os.path.realpath(__file__)))
from spider.Spider import Spider  
from spider.chain.material.MaterialCrawlerChain  import MaterialCrawlerChain  
 
class MaterialSpider(Spider):
  '''
  Get the full material, go list page and go the detail page
  '''
  
  def get_chain(self):
    return MaterialCrawlerChain()

  def get_items(self):
    material = self.request.get('material')
    return [material] if material else None
  
  def get_message(self):
    items = self.get_items()
    if not items:
      message = 'Crawled material failure'
    else:
      message = 'Crawled material successfully' 
      message+=self.__get_item(items[0])
    return message
  
  def __get_item(self,item):
    article = '\n\nArticle :'
    article += "\n\n%s" % item['material_title']
    
    body = json.loads(item['material_body'])
    body = json.dumps(body, indent=2, ensure_ascii=False)
    article += "\n%s" % body
    return article

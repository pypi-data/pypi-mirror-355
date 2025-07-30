import sys,os,re
from .MaterialCrawler import MaterialCrawler  
from .MaterialParaImage import MaterialParaImage  
from .MaterialExtender import MaterialExtender  
from .MaterialFilter import MaterialFilter  

sys.path.append(re.sub('blues_lib.*','blues_lib',os.path.realpath(__file__)))
from spider.chain.CrawlerHandler import CrawlerHandler

class MaterialCrawlerChain(CrawlerHandler):
  '''
  Basic behavior chain, it's a handler too
  '''
  def resolve(self,request):
    '''
    Deal the atom by the event chain
    '''
    if not request or not request.get('schema') or not request.get('browser') or not request.get('brief'):
      return

    handler = self.__get_chain()
    handler.handle(request)

  def __get_chain(self):
    '''
    Converters must be executed sequentially
    '''
    # writer
    crawler = MaterialCrawler()
    para_image = MaterialParaImage()
    extender = MaterialExtender()
    filtee = MaterialFilter()

    crawler.set_next(para_image) \
      .set_next(extender) \
      .set_next(filtee)

    return crawler

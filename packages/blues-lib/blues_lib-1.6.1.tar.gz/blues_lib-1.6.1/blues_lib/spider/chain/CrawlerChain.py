import sys,os,re
from .CrawlerHandler import CrawlerHandler  
sys.path.append(re.sub('blues_lib.*','blues_lib',os.path.realpath(__file__)))
from spider.chain.CrawlerHandler import CrawlerHandler  
from spider.chain.MaterialsCrawler import MaterialsCrawler  
from spider.chain.brief.BriefCrawlerChain import BriefCrawlerChain  

class CrawlerChain(CrawlerHandler):
  '''
  Basic behavior chain, it's a handler too
  '''
  kind = 'chain'

  def resolve(self,request):
    '''
    Deal the atom by the event chain
    '''
    handler = self.__get_chain()
    handler.handle(request)

  def __get_chain(self):
    '''
    Converters must be executed sequentially
    '''
    # writer
    brief_chain = BriefCrawlerChain()
    material_crawler = MaterialsCrawler()
    
    # must inovke the extender before the filter
    brief_chain.set_next(material_crawler)

    return brief_chain

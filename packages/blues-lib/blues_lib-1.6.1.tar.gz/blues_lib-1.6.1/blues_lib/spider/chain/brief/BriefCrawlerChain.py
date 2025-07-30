import sys,os,re
from .BriefCrawler import BriefCrawler  
from .BriefExtender import BriefExtender  
from .BriefThumbnail import BriefThumbnail  
from .BriefFilter import BriefFilter  

sys.path.append(re.sub('blues_lib.*','blues_lib',os.path.realpath(__file__)))
from spider.chain.CrawlerHandler import CrawlerHandler

class BriefCrawlerChain(CrawlerHandler):
  '''
  Basic behavior chain, it's a handler too
  '''
  
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
    brief_crawler = BriefCrawler()
    brief_extender = BriefExtender()
    brief_thumbnail= BriefThumbnail()
    brief_filter = BriefFilter()
    
    # must inovke the extender before the filter
    brief_crawler.set_next(brief_extender) \
      .set_next(brief_thumbnail) \
      .set_next(brief_filter)

    return brief_crawler

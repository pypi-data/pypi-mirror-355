import sys,re,os
sys.path.append(re.sub('blues_lib.*','blues_lib',os.path.realpath(__file__)))
from spider.Spider import Spider  
from spider.chain.CrawlerChain  import CrawlerChain  
 
class MaterialsSpider(Spider):
  '''
  Get the valid material list, use to crawl the info that don't need to go to the detail page
  Such as gallery list.
  '''

  def get_chain(self):
    return CrawlerChain()

  def get_items(self):
    return self.request.get('materials')

  def get_message(self):
    items = self.get_items()
    count = len(items) if items else 0
    message = 'Crawled [%s] materials totally' % count
    if count>0:
      message+=self.__get_titles(items)
    return message

  def __get_titles(self,items):
    titles = ''
    i = 1
    for item in items:
      titles+='\n %s. %s' % (i,item.get('material_title'))
      i+=1
    return titles


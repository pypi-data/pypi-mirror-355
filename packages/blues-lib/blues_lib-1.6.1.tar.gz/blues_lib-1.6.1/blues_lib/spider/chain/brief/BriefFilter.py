import sys,os,re
sys.path.append(re.sub('blues_lib.*','blues_lib',os.path.realpath(__file__)))
from spider.chain.CrawlerHandler import CrawlerHandler
from deco.LogDeco import LogDeco
from pool.BluesMaterialIO import BluesMaterialIO  

class BriefFilter(CrawlerHandler):
  '''
  Remove the unavailable breifs
  '''
  action = 'filter'
  
  @LogDeco()
  def resolve(self,request):
    if not request or not request.get('briefs'):
      return
    
    request['briefs'] = self.__filter(request)

  def __set_message(self,typed_briefs):
    counts = (len(typed_briefs['available']),len(typed_briefs['illegal']),len(typed_briefs['exist']))
    self.message = 'Filter briefs : available-[%s] illegal-[%s] exist-[%s]' % counts

  def __filter(self,request):
    briefs = request.get('briefs')
    typed_briefs = {
      'illegal':[],
      'exist':[],
      'available':[],
    } 

    for brief in briefs:
      if not BluesMaterialIO.is_legal_brief(brief):
        typed_briefs['illegal'].append(brief)
        continue

      if BluesMaterialIO.exist(brief):
        typed_briefs['exist'].append(brief)
        continue

      typed_briefs['available'].append(brief)

    self.__set_message(typed_briefs)
    return typed_briefs['available'] if typed_briefs['available'] else None

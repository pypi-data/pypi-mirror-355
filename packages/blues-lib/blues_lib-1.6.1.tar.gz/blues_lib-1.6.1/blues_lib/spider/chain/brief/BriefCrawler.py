import sys,os,re
sys.path.append(re.sub('blues_lib.*','blues_lib',os.path.realpath(__file__)))
from spider.chain.CrawlerHandler import CrawlerHandler
from deco.LogDeco import LogDeco
from sele.behavior.BehaviorChain import BehaviorChain

class BriefCrawler(CrawlerHandler):
  '''
  Replace the schema's placeholder by data
  '''
  @LogDeco()
  def resolve(self,request):
    '''
    Parameter:
      request {dict} : schema,count,briefs,materials
    '''
    if not request or not request.get('schema') or not request.get('browser'):
      return

    briefs = self._crawl(request)
    request['briefs'] = briefs
    count = len(briefs) if briefs else 0
    self._set_message(count)
    
  def _set_message(self,count):
    self.message = 'Crawl [%s] briefs' % count    
  
  def _crawl(self,request):
    browser = request.get('browser')
    schema = request.get('schema')
    url = schema.basic.get('brief_url')
    browser.open(url) 

    self._prepare(browser,schema)
    data = self._execute(browser,schema)
    self._clean(browser,schema)
    return data

  def _prepare(self,browser,schema):
    if schema.brief_preparation:
      handler = BehaviorChain(browser,schema.brief_preparation)
      handler.handle()

  def _execute(self,browser,schema):
    if schema.brief_execution:
      handler = BehaviorChain(browser,schema.brief_execution)
      outcome = handler.handle()
      return outcome.data
    else:
      return None

  def _clean(self,browser,schema):
    if schema.brief_cleanup:
      handler = BehaviorChain(browser,schema.brief_cleanup)
      handler.handle()

  
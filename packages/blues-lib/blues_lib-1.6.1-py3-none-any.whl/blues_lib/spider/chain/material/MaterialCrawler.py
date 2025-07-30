import sys,os,re
sys.path.append(re.sub('blues_lib.*','blues_lib',os.path.realpath(__file__)))
from spider.chain.CrawlerHandler import CrawlerHandler
from deco.LogDeco import LogDeco
from sele.behavior.BehaviorChain import BehaviorChain
from pool.BluesMaterialIO import BluesMaterialIO  

class MaterialCrawler(CrawlerHandler):
  '''
  Replace the schema's placeholder by data
  '''
  name = __name__

  @LogDeco()
  def resolve(self,request):
    '''
    Get one material by one brief
    Parameter:
      request {dict} : schema,count,brief,material
    '''
    if (not request 
        or not request.get('schema') 
        or not request.get('browser') 
        or not request.get('brief')):
      return

    request['material'] = self._crawl(request)
  
  def _crawl(self,request):
    browser = request.get('browser')
    schema = request.get('schema')
    brief = request.get('brief')

    url = BluesMaterialIO.get_material_url(brief)
    if not url:
      return

    try:
      browser.open(url)

      self._prepare(browser,schema)
      outcome = self._execute(browser,schema)
      self._clean(browser,schema)
      material = outcome.data
      # STDOut
      # convert genenal lines to the format body
      material['material_body'] = self._get_format_body(material['material_body'])
      if BluesMaterialIO.is_legal_detail(material):
        # here merge the breif and the material
        return {**brief,**material}
      else:
        self._sign_unavail(brief,outcome.message)
        return None
    except Exception as e:
      print('error',e)
      self._sign_unavail(brief,e)
      return None
    
  def _prepare(self,browser,schema):
    if schema.material_preparation:
      handler = BehaviorChain(browser,schema.material_preparation)
      handler.handle()

  def _execute(self,browser,schema):
    handler = BehaviorChain(browser,schema.material_execution)
    return handler.handle()

  def _clean(self,browser,schema):
    if schema.material_cleanup:
      handler = BehaviorChain(browser,schema.material_cleanup)
      handler.handle()

  def _get_format_body(self,lines):
    '''
    Get the format material body paras from the general lines
    '''
    paras = []
    for idx,value in enumerate(lines):
      if value.get('image'):
        paras.append({'type':'image','value':value['image']})
      else:
        paras.append({'type':'text','value':value['text']})
    return paras

  def _sign_unavail(self,brief,error):
    '''
    Sign the unavail material to db, avoid to retry next time
    '''
    url = brief.get('material_url')
    title = brief.get('material_title',url)
    
    message = ''
    message +='Crawl [%s] material failed : %s' % (title,error)

    # sign unavail to avoid to refetch 
    entity = {**brief}
    entity['material_status'] = 'illegal'
    result = BluesMaterialIO.insert(entity)
    if result['code'] == 200:
      message+= '; Signed unavail successfully'
      self._logger.info(message)
    else:
      message+= '; Signed unavail failure'
      self._logger.error(message)
    
    return result.get('count',0)

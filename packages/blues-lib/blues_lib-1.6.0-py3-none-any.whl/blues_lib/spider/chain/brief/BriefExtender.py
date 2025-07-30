import sys,os,re
sys.path.append(re.sub('blues_lib.*','blues_lib',os.path.realpath(__file__)))
from spider.chain.CrawlerHandler import CrawlerHandler
from deco.LogDeco import LogDeco
from util.BluesAlgorithm import BluesAlgorithm 

class BriefExtender(CrawlerHandler):
  '''
  Extend the required fields by existed fields
  '''
  @LogDeco()
  def resolve(self,request):
    if not request or not request.get('briefs'):
      return
    self.__extend(request)
    
  def __set_message(self,count):
    self.message = 'Extend [%s] briefs' % count    

  def __extend(self,request):
    schema = request.get('schema')
    briefs = request.get('briefs')
    site = schema.basic.get('site')
    mode = schema.basic.get('mode')
    lang = schema.basic.get('lang')
    count = 0
    for brief in briefs:
      count+=1
      brief['material_type'] = mode # article gallery shortvideo qa
      brief['material_site'] = site # ifeng bbc
      brief['material_lang'] = lang # cn en
      brief['material_id'] = site+'_'+BluesAlgorithm.md5(brief['material_url'])

    self.__set_message(count)
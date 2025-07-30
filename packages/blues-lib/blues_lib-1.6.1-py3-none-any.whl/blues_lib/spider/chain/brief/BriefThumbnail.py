import sys,os,re
sys.path.append(re.sub('blues_lib.*','blues_lib',os.path.realpath(__file__)))
from deco.LogDeco import LogDeco
from spider.chain.CrawlerHandler import CrawlerHandler
from pool.BluesMaterialIO import BluesMaterialIO

class BriefThumbnail(CrawlerHandler):
  '''
  Extend the required fields by existed fields
  '''
  @LogDeco()
  def resolve(self,request):
    if not request or not request.get('briefs'):
      return
    
    self.__download(request)

  def __set_message(self,count):
    self.message = 'Download [%s] brief thumbnails' % count    

  def __download(self,request):
    briefs = request.get('briefs')
    count = 0
    for brief in briefs:
      # convert online image to local image
      local_image = BluesMaterialIO.get_download_thumbnail(brief)
      if local_image:
        count+=1
        brief['material_thumbnail'] = local_image

    self.__set_message(count)

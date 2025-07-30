import sys,os,re
sys.path.append(re.sub('blues_lib.*','blues_lib',os.path.realpath(__file__)))
from deco.LogDeco import LogDeco
from spider.chain.CrawlerHandler import CrawlerHandler
from pool.BluesMaterialIO import BluesMaterialIO

class MaterialParaImage(CrawlerHandler):
  '''
  Extend the required fields by existed fields
  '''
  @LogDeco()
  def resolve(self,request):
    if not request or not request.get('material'):
      return
    
    self.__download(request)

  def __set_message(self,count):
    self.message = 'Download [%s] material images' % count    

  def __download(self,request):
    material = request.get('material')
    schema = request.get('schema')
    paras = material.get('material_body')
    max_image_count = schema.limit.get('max_material_image_count')
    image_count = 0
    first_image = None

    if not paras:
      return

    for para in paras:
      # download and deal image
      if para['type'] != 'image':
        continue

      local_image = BluesMaterialIO.get_download_image(material,para['value'])
      if not local_image:
        continue

      para['value'] = local_image
      if not first_image:
        first_image = local_image    

      image_count+=1
      if image_count>=max_image_count:
        break

    self.__set_message(image_count)
    self.__pad_image(material,first_image)
    self.__pad_thumbnail(material,first_image)

  def __pad_image(self,material,first_image):
    material_thumbnail = material.get('material_thumbnail')
    paras = material.get('material_body')
    if not first_image and material_thumbnail:
      paras.append({'type':'image','value':material_thumbnail})
  
  def __pad_thumbnail(self,material,first_image):
    if not material.get('material_thumbnail') and first_image:
      material['material_thumbnail'] = first_image

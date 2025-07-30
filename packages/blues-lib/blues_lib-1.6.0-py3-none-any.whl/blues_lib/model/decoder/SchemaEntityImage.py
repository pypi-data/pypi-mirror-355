import sys,os,re
sys.path.append(re.sub('blues_lib.*','blues_lib',os.path.realpath(__file__)))
from model.decoder.DecoderHandler import DecoderHandler
from atom.Atom import Atom
from pool.BluesMaterialIO import BluesMaterialIO
from util.BluesFiler import BluesFiler
from util.BluesImager import BluesImager
from util.BluesConsole import BluesConsole

class SchemaEntityImage(DecoderHandler):
  '''
  Replace the schema's placeholder by data
  '''
  kind = 'handler'

  def resolve(self,request):
    '''
    Parameter:
      request {dict} : the schema and value dict, such as:
        {'atom':Atom, 'value':dict}
    '''
    if not request or not request.get('schema') or not request.get('material'):
      return request

    
    self.__replace_thumbnail(request)
    self.__replace_images(request)
    self.__limit_image(request)
    return request

  def __limit_image(self,request):
    '''
    Replace the placeholder value in the atom
    Parameter:
      entity {dict} : the key is the placeholder, the value is the real value
    '''
    limit = request['schema'].limit
    material = request['material']
    # Only support to replace the atom's vlue
    image_max_length = limit.get('image_max_length')
    material_body_image = material.get('material_body_image')
    if image_max_length and material_body_image:
      material['material_body_image'] = material_body_image[:image_max_length]

  def __replace_thumbnail(self,request):
    material = request['material']
    material_thumbnail = material.get('material_thumbnail')
    if not BluesFiler.exists(material_thumbnail):
      material['material_thumbnail'] = self.__get_default_thumbnail(material)
      BluesConsole.info('material_thumbnail do not exists, use the default image')

  def __get_default_thumbnail(self,material):
    material_body_image = material.get('material_body_image')
    if material_body_image and BluesFiler.exists(material_body_image[0]):
      return material_body_image[0]
    else:
      return self.__get_online_image()

  def __get_default_image(self,material):
    material_thumbnail = material.get('material_thumbnail')
    if material_thumbnail and BluesFiler.exists(material_thumbnail):
      return material_thumbnail
    else:
      return self.__get_online_image()
      
  def __replace_images(self,request):
    material = request['material']
    material_body_image = material.get('material_body_image')
    exists_images = []
    for image in material_body_image: 
      if not BluesFiler.exists(image):
        continue
      ratio = BluesImager.get_wh_ratio(image)
      # remove the AD banner image, width/height > 4
      if ratio>4:
        continue
      exists_images.append(image)

    if not exists_images:
      exists_images.append(self.__get_default_image(material))
      BluesConsole.info('material_body_image do not exists, use the default image')

    material['material_body_image'] = exists_images

  def __get_online_image(self):
    online_image = 'http://deepbluenet.com/naps/breaking-news.png'
    local_dir = BluesMaterialIO.get_material_root()
    response = BluesFiler.download(online_image,local_dir)
    if response['code']==200:
      return response['files'][0]
    else:
      return ''
      








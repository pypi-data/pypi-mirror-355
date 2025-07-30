import sys,os,re,datetime
from .BluesFilePool import BluesFilePool

sys.path.append(re.sub('blues_lib.*','blues_lib',os.path.realpath(__file__)))
from util.BluesType import BluesType    
from util.BluesDateTime import BluesDateTime    
from util.BluesURL import BluesURL    
from util.BluesImage import BluesImage    
from util.BluesFiler import BluesFiler    
from util.BluesConsole import BluesConsole    
from sql.BluesSQLIO import BluesSQLIO    

class BluesMaterial(BluesFilePool):
  
  # the material stack's root dir
  MATERIAL_DIR = 'material'
  MATERIAL_LOG_DIR = 'log'

  # the material statck's file
  STACK_FILE_NAME = 'stack.json'
  DETAIL_FILE_NAME = 'detail.json'
  DEFAULT_THUMBNAIL = 'thumbnail.jpg'

  __LOCAL_SQL_CONFIG = {
    'host':'localhost',
    'user':'root',
    'password':'',
    'database':'naps',
  }

  __SQL_CONFIG = {
    'host':'xdm721917656.my3w.com',
    'user':'xdm721917656',
    'password':'beastmaster2020.',
    'database':'xdm721917656_db',
  }
  REQUIRED_BRIEF_FIELDS = ['material_id','material_site','material_title','material_url']
  REQUIRED_DETAIL_FIELDS = ['material_body']
  REQUIRED_TOTAL_FIELDS = ['material_id','material_site','material_title','material_url','material_thumbnail','material_body']

  MATERIAL_TABLE = 'naps_material'
  MATERIAL_URL_KEY = 'material_url'
  
  MATERIAL_LOG_TABLE = 'naps_published_log'
  SQL_EXECUTOR = BluesSQLIO(__SQL_CONFIG)

  @classmethod
  def get_default_thumbnail(cls):
    return BluesURL.get_file_path(cls.get_stack_root(),cls.DEFAULT_THUMBNAIL)
  
  @classmethod
  def get_screenshot_dir(cls,dirs=[]):
    today = BluesDateTime.get_today()
    subdirs = [cls.MATERIAL_LOG_DIR,today,*dirs]
    return cls.get_dir_path(subdirs)

  @classmethod
  def get_download_dir(cls,dirs=[]):
    today = BluesDateTime.get_today()
    subdirs = [cls.MATERIAL_DIR,today,*dirs]
    return cls.get_dir_path(subdirs)

  @classmethod
  def get_download_thumbnail(cls,material):
    '''
    Don't use the default thumbnail
    '''
    material_thumbnail = material.get('material_thumbnail')
    if not material_thumbnail:
      return None

    download_image = cls.get_download_image(material,material_thumbnail)
    if download_image:
      return download_image
    else:
      return None
  
  @classmethod
  def get_download_image(cls,material,image_url):
    '''
    Download the image in the body
    Parameter:
      material {Dict} : a standard material dict
      image_url {str} : the image's online url
    '''
    material_id = material.get('material_id')
    material_site = material.get('material_site')
    image_dir = cls.get_download_dir([material_site,material_id])
    result = BluesFiler.download_one(image_url,image_dir)
    if result[0]==200:
      # convert type and size
      download_path = result[1]
      # the filename may be changed
      converted_path = BluesImage.convert_type(download_path)
      BluesImage.convert_size(converted_path)
      BluesConsole.success('Converted the image type and size: %s' % converted_path)
      return converted_path
    else:
      return None

  @classmethod
  def get_material_url(cls,entity):
    '''
    Get the material page url from the brief or mateiral entity
    '''
    return entity.get(cls.MATERIAL_URL_KEY)
  
  @classmethod
  def is_legal_brief(cls,entity):
    if not entity:
      return False
    return BluesType.is_field_satisfied_dict(entity,cls.REQUIRED_BRIEF_FIELDS,True)

  @classmethod
  def is_legal_detail(cls,entity):
    if not entity:
      return False
    return BluesType.is_field_satisfied_dict(entity,cls.REQUIRED_DETAIL_FIELDS,True)

  @classmethod
  def is_legal_material(cls,entity):
    if not entity:
      return False
    return BluesType.is_field_satisfied_dict(entity,cls.REQUIRED_TOTAL_FIELDS,True)

  @classmethod
  def get_legal_briefs(cls,briefs):
    return cls.__get_legal_entities(briefs,cls.is_legal_brief)

  @classmethod
  def get_legal_materials(cls,meterials):
    return cls.__get_legal_entities(meterials,cls.is_legal_material)

  @classmethod
  def __get_legal_entities(cls,entities,legal_func):
    legal_entities = []
    for entity in entities:
      if legal_func(entity):
        legal_entities.append(entity)
    return legal_entities
  
  @classmethod
  def get_output(cls,code=200,message='success'):
    return {
      'code':code,
      'message':message,
    }

  @classmethod
  def get_stack_file(cls):
    return cls.get_file_path(cls.MATERIAL_DIR,cls.STACK_FILE_NAME)
  
  @classmethod
  def get_stack_root(cls):
    return cls.get_dir_path(cls.MATERIAL_DIR)

  @classmethod
  def get_material_root(cls):
    return cls.get_dir_path(cls.MATERIAL_DIR)

  @classmethod
  def get_log_root(cls):
    return cls.get_dir_path(cls.MATERIAL_LOG_DIR)

  @classmethod
  def is_valid_brief(cls,brief):
    if not brief:
      return False
    fields = ['site','id','path']
    return BluesType.is_field_satisfied_dict(brief,fields,True)

  @classmethod
  def is_valid_new_brief(cls,brief):
    if not brief:
      return False
    fields = ['site','id']
    return BluesType.is_field_satisfied_dict(brief,fields,True)

  @classmethod
  def is_valid_detail(cls,detail):
    if not detail:
      return False
    fields = ['url','id','title','datetime','body']
    return BluesType.is_field_satisfied_dict(detail,fields,True)

  @classmethod
  def get_new_detail_path(cls,brief):
    '''
    Base the site and id, create the detail's json file path
    Parameter:
      brief {dict} : the brief dict that path has no value
    Returns:
      {str} : the standard detail file path, such as : c:/blues_lib/material/ifeng.com/id3/detail.json
    '''

    subdirs = [cls.get_stack_root(),brief.get('site'),brief.get('id')]
    dir_path = cls.get_dir_path(subdirs)
    if not BluesFiler.exists(dir_path):
      BluesFiler.makedirs(dir_path)

    return cls.get_file_path(dir_path,cls.DETAIL_FILE_NAME)
    

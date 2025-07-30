import sys,os,re,json
from .Material import Material

sys.path.append(re.sub('blues_lib.*','blues_lib',os.path.realpath(__file__)))
from pool.BluesMaterialIO import BluesMaterialIO

class DBMaterial(Material):
  '''
  The material from db
  '''
  # override
  def first(self,query_condition):
    query_condition['count'] = 1
    rows = self.get(query_condition) 
    return rows[0] if rows else None

  # override
  def get(self,query_condition):
    mode = query_condition.get('mode')
    count = query_condition.get('count')
    material_type = query_condition.get('material_type')
    rows = None

    if mode == 'latest':
      rows = self.__latest(count,material_type)
      if rows:
        self.__format(rows) 

    return rows

  def __latest(self,count=1,material_type=''):
    response = BluesMaterialIO.latest(count,material_type)
    return response.get('data')

  def __format(self,rows):
    '''
    Set the foramt entity dict, extract the json fields to object
    Returns 
      {list<dict>}
    '''
    for material in rows:
      material_body_text = material.get('material_body_text')
      material_ai_body_text = material.get('material_ai_body_text')
      material_body_image = material.get('material_body_image')
      material_body = material.get('material_body')

      material_title = material.get('material_title')
      material_thumbnail = material.get('material_thumbnail')

      if material_body_text:
        texts = json.loads(material_body_text)
      else:
        texts = None

      if material_ai_body_text:
        ai_texts = json.loads(material_ai_body_text)
      else:
        ai_texts = None

      if material_body_image:
        images = json.loads(material_body_image)
      else:
        images = [material_thumbnail]

      if material_body:
        body = json.loads(material_body)
      else:
        body = [
          {'type':'text','value':material_title},
          {'type':'image','value':material_thumbnail},
        ]
      
      # convert the json to object
      material['material_body_text']=texts
      material['material_ai_body_text']=ai_texts
      material['material_body_image']=images
      material['material_body']=body


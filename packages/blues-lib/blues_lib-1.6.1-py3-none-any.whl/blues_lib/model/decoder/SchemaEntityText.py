import sys,os,re
sys.path.append(re.sub('blues_lib.*','blues_lib',os.path.realpath(__file__)))
from model.decoder.DecoderHandler import DecoderHandler

class SchemaEntityText(DecoderHandler):
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
    
    self.__limit_content(request)
    self.__limit_title(request)

    return request

  def __limit_content(self,request):
    '''
    Replace the placeholder value in the atom
    Parameter:
      entity {dict} : the key is the placeholder, the value is the real value
    '''
    schema = request['schema']
    basic = request['schema'].basic
    limit = request['schema'].limit
    material = request['material']

    # Only support to replace the atom's vlue
    content_max_length = limit.get('content_max_length',5000)

    material_body_text = None
    if basic.get('field') == 'ai':
      material_body_text = material.get('material_ai_body_text')
    else:
      material_body_text = material.get('material_body_text')

    material_body_image = material.get('material_body_image')

    material_title = ''
    if basic.get('field') == 'ai':
      material_title = material.get('material_ai_title')
    else:
      material_title = material.get('material_title')

    material_type = material.get('material_type')
    material_para = []

    if material_body_text:
      # add title to the content in the events channel
      if schema.channel=='events' and material_type!='gallery':
        material_body_text.insert(0,'【%s】' % material_title)

      limit_material_body_text = []
      length = 0
      index = 0
      for para in material_body_text:
        if length<content_max_length:
          # must add a \n to break the line
          line=para
          if schema.channel=='article':
            line+='\n'

          limit_material_body_text.append(line)
          
          # set para
          para = {
            'text':line,
            'image':'',
          }
          if len(material_body_image)>=index+1:
            para['image'] = material_body_image[index]

          material_para.append(para)
          length += len(line)
          
        index+=1

      material['material_body_text'] = limit_material_body_text
      material['material_para'] = material_para

  def __limit_title(self,request):
    '''
    Replace the placeholder value in the atom
    Parameter:
      entity {dict} : the key is the placeholder, the value is the real value
    '''
    basic = request['schema'].basic
    limit = request['schema'].limit
    material = request['material']

    # Only support to replace the atom's vlue
    title_max_length = limit.get('title_max_length',28)
    material_title = ''
    if basic.get('field') == 'ai':
      material_title = material.get('material_ai_title')
    else:
      material_title = material.get('material_title')

    if len(material_title)>title_max_length:
      end_index = title_max_length-3
      limit_material_title = material_title[:end_index]+'...'
      material['material_title'] = limit_material_title
    else:
      material['material_title'] = material_title





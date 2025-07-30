import sys,os,re,json 
sys.path.append(re.sub('blues_lib.*','blues_lib',os.path.realpath(__file__)))
from deco.LogDeco import LogDeco
from spider.chain.CrawlerHandler import CrawlerHandler

class MaterialExtender(CrawlerHandler):
  '''
  Extend the required fields by existed fields
  '''
  @LogDeco()
  def resolve(self,request):
    if not request or not request.get('material'):
      return
    
    self.__extend(request)

  def __set_message(self,paras):
    if not paras:
      self.message = 'Extend failure: no paras'
    else:
      self.message = 'Extend successfully'

  def __extend(self,request):
    material = request.get('material')
    paras = material.get('material_body')

    self.__set_message(paras)

    if not paras:
      return

    body_dict = self.__get_body_dict(paras)

    # append extend fields
    material['material_body_text'] = json.dumps(body_dict['text'],ensure_ascii=False)
    material['material_body_image'] = json.dumps(body_dict['image'],ensure_ascii=False)

    # convert the dict to json
    material['material_body'] = json.dumps(material['material_body'],ensure_ascii=False)

  def __get_body_dict(self,paras):
    body_dict = {
      'text':[],
      'image':[],
    }
    for para in paras:
      body_dict[para['type']].append(para['value'])
    
    return body_dict





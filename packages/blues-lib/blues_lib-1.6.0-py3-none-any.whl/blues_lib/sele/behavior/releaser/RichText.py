import sys,os,re,copy

sys.path.append(re.sub('blues_lib.*','blues_lib',os.path.realpath(__file__)))

from sele.behavior.Behavior import Behavior
from type.output.STDOut import STDOut

# only need Array
from sele.behavior.composite.Array import Array  

# decorator
from sele.behavior.deco.BehaviorDeco import BehaviorDeco

class RichText(Behavior):

  @BehaviorDeco(False,True)
  def resolve(self):
    '''
    It's a Behavior subclass
    It deal a atom list
    '''
    if self.kind!='richtext':
      return False 
    
    if type(self.value)!=dict:
      return STDOut(502,'value is not a dict')

    # check value structure 
    image_atom = self.value.get('image_atom')
    text_atom = self.value.get('text_atom')
    image_value_atom = self.value.get('image_value')
    text_value_atom = self.value.get('text_value')
    image_value = image_value_atom.get_value() if image_value_atom else None
    text_value = text_value_atom.get_value() if text_value_atom else None

    if not text_atom:
      return STDOut(503,'The text atom is None')

    if not image_atom:
      return STDOut(504,'The image atom is None')
    
    i = 0
    for text in text_value:
      self.__handle_atom(text_atom,'material_body_text',text)
      if len(image_value)>i:
        image = image_value[i]
        self.__handle_atom(image_atom,'material_body_image',image)

      i+=1 
    
    return STDOut()

  def __handle_atom(self,atom,key,value):
    copy_of_atom = self.__get_copy_of_array_atom(atom,key,value)
    # replace the atom's select to current unit's web_element
    handler = Array(self.browser,copy_of_atom)
    handler.handle()

  def __get_copy_of_array_atom(self,array_atom,key,value):
    '''
    copyt and replace the text or image value
    Parameters:
      array_atom {ArrayAtom} : the aim atom
      key {str} : the current value, will be replaced
      value {str} : the real materail field value
    '''
    copy_of_array_atom = copy.deepcopy(array_atom)
    for atom in copy_of_array_atom.get_value():
      # set a selector firstly
      if atom.get_value()==key:
        atom.set_value(value)

    return copy_of_array_atom

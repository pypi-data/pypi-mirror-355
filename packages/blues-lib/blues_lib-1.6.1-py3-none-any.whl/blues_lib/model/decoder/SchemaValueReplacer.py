import sys,os,re
sys.path.append(re.sub('blues_lib.*','blues_lib',os.path.realpath(__file__)))
from model.decoder.DecoderHandler import DecoderHandler
from atom.Atom import Atom

class SchemaValueReplacer(DecoderHandler):
  '''
  Replace the schema's palceholder by data
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

    self.__fill_value(request)

    return request

  def __fill_value(self,request):
    '''
    Replace the placeholder value in the atom
    Parameter:
      entity {dict} : the key is the placeholder, the value is the real value
    '''
    material = request['material']
    schema = request['schema']
    atoms = self._get_decode_atoms(schema)

    # support input a atom list
    for atom in atoms:
      self.__set_atom_value(atom,material)

  def __set_atom_value(self,atom_node,entity):
    if not atom_node:
      return
    
    # only deal with atom node
    if not isinstance(atom_node,Atom):
      return

    atom_value = atom_node.get_value()

    if isinstance(atom_value,list):
      idx = 0
      for sub_atom_value in atom_value:
        if isinstance(sub_atom_value,Atom):
          self.__set_atom_value(sub_atom_value,entity)
        else:
          atom_value[idx] = self.__get_replaced_value(sub_atom_value,entity)
        idx+=1
      
    elif isinstance(atom_value,dict):
      for key,sub_atom_value in atom_value.items():
        if isinstance(sub_atom_value,Atom):
          self.__set_atom_value(sub_atom_value,entity)
        else:
          atom_value[key] = self.__get_replaced_value(sub_atom_value,entity)

    elif isinstance(atom_value,str):
      atom_node.set_value(self.__get_replaced_value(atom_value,entity))

  def __get_replaced_value(self,placeholder,entity):
    if not ( type(placeholder)==str) or not placeholder or not entity:
      return placeholder 

    # pattern matched
    if not re.search(r'^\$\{.+\}$',placeholder):
      return placeholder
    
    replaced_value = placeholder
    for key in entity:
      pattern = r'^\$\{'+key+r'\}$'

      if not re.search(pattern,placeholder):
        continue

      value = entity.get(key)
      # replace the placehoder
      replaced_value = value
      break

    return replaced_value



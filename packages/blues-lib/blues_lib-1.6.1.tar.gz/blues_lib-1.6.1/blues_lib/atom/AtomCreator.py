import sys,os,re,copy,inspect
sys.path.append(re.sub('blues_lib.*','blues_lib',os.path.realpath(__file__)))
from atom.AtomFactory import AtomFactory

class AtomCreator():
  
  factory = AtomFactory()

  @classmethod 
  def create(cls,meta:dict):
    '''
    Convert any atom meta to the Atom Object
    @param {dict} meta: a valid meta dict (must has the attr of 'kind'), such as:
      {"kind":"url","title":"homepage","value":"https://baidu.com"} 
    '''
    meta_copy = copy.deepcopy(meta)
    return cls._convert(meta_copy)

  @classmethod 
  def _convert(cls,meta):
    '''
    convert a specify meta to a Atom
    '''
    if not isinstance(meta,dict):
      return meta

    # deal the nest atom value
    kind = meta.get('kind')
    value = meta.get('value')
    if not kind:
      return meta

    if isinstance(value,list) or isinstance(value,tuple):
      for item_idx,item_val in enumerate(value):
        value[item_idx] = cls._convert(item_val)
    elif isinstance(value,dict):
      for key,val in value.items():
        value[key] = cls._convert(val)

    method_name = cls._get_method_name(kind,cls.factory)
    method = getattr(cls.factory, method_name)

    del meta['kind']
    if method:
      return method(**meta)
    else:
      return meta


  @classmethod
  def _get_method_name(cls,type_str: str,factory:AtomFactory) -> str:
    """根据类型字符串动态匹配工厂类中的创建方法名。

    该方法会查找工厂类中所有以'create_'开头的方法，并将后缀部分与输入的类型字符串进行不区分大小写的匹配。

    Args:
      type_str: 要匹配的类型字符串（全小写格式，如'textarea'）
      factory: 包含create_前缀方法的工厂类实例

    Returns:
      匹配的完整方法名称字符串，如'create_textArea'。若未找到匹配则返回None

    Example:
      >>> class AtomFactory:
      ...   def create_textArea(self): pass
      >>> get_method('textarea', AtomFactory())
      'create_textArea'
    """
    type_lower = type_str.lower()
    for name, method in inspect.getmembers(factory, inspect.ismethod):
      if name.startswith('create_'):
        suffix = name[len('create_'):]
        if suffix.lower() == type_lower:
          return name
    return None
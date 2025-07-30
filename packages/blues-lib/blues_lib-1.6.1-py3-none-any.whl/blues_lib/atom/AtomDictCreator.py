from .AtomCreator import AtomCreator

class AtomDictCreator():

  @classmethod
  def create(cls,meta_dict):
    '''
    Convert a dict's all attributes to atoms
    '''
    atom_meta = meta_dict.copy()
    for key,value in atom_meta.items():
      atom_meta[key] = AtomCreator.create(value)
      
    return atom_meta

    
    

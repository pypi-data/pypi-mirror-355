import sys,os,re
sys.path.append(re.sub('blues_lib.*','blues_lib',os.path.realpath(__file__)))
from sql.BluesSQLIO import BluesSQLIO    

class DBTableIO():
  '''
  Based on SQL, manage the input and output of materials.
  '''
  __SQL_CONFIG = {
    'host':'xdm721917656.my3w.com',
    'user':'xdm721917656',
    'password':'beastmaster2020.',
    'database':'xdm721917656_db',
  }
  SQL_EXECUTOR = BluesSQLIO(__SQL_CONFIG)

  def __init__(self,table):
    self.table = table

  def get(cls,fields=None,conditions=None,orders=None,pagination=None):
    '''
    Query rows
    Parameter:
      fields {list<str>} : the table fields 
      conditions {dict | list<dict>} : the standard condition value ,like:
        {'field':'material_id','comparator':'=','value':'id2'} 
        [{'field':'material_id','comparator':'=','value':'id2'}]
      orders {dict | list<dict>} : the standard order by dict, like:
        {'field':'material_status','sort':'asc'}
        [{'field':'material_status','sort':'asc'}]
      pagination {dict} : the standard pager dict, like:
        {'no':1,'size':10}
    Return:
      {dict} : the standard sql output,like:
         {'code': 200, 'count': 1, data: [{},{}],'sql': 'select xxx'}
    '''
    return cls.SQL_EXECUTOR.get(cls.table,fields,conditions,orders,pagination)

  def post(cls,fields,values):
    '''
    Insert one more multi rows
    Parameter:
      fields {list<str>} : the table fields 
      values {list<list<str>>} : two-dim list, every list is a row field value
        the fields' length must be equal to the values row list's length
    Return:
      {dict} : the standard sql output,like:
         {'code': 200, 'count': 1, 'sql': 'insert xxx'}
    '''
    return cls.SQL_EXECUTOR.post(cls.table,fields,values)
  
  def insert(cls,entities):
    '''
    Insert one more multi rows
    Parameter:
      entities {dict | list<dict>} : every dict contains field:value
    Return:
      {dict} : the standard sql output,like:
         {'code': 200, 'count': 1, 'sql': 'insert xxx'}
    '''
    return cls.SQL_EXECUTOR.insert(cls.table,entities)


  def put(cls,fields,values,conditions=None):
    '''
    Update one or multi rows
    Parameter:
      fields {list<str>} : the table fields 
      values {list<any>} : the updated value
        the value's list length should be equal to the field's list length
      conditions {dict | list<dict>} : the standard condition value ,like:
        {'field':'material_id','comparator':'=','value':'id2'} 
        [{'field':'material_id','comparator':'=','value':'id2'}]
    Return:
      {dict} : the standard sql output,like:
         {'code': 200, 'count': 1, 'sql': 'update xxx'}
    '''
    return cls.SQL_EXECUTOR.put(cls.table,fields,values,conditions)

  def update(cls,entity,conditions=None):
    '''
    Update one or multi rows
    Parameter:
      entity {dict} : every update dict
      conditions {dict | list<dict>} : the standard condition value ,like:
        {'field':'material_id','comparator':'=','value':'id2'} 
        [{'field':'material_id','comparator':'=','value':'id2'}]
    Return:
      {dict} : the standard sql output,like:
         {'code': 200, 'count': 1, 'sql': 'update xxx'}
    '''
    return cls.SQL_EXECUTOR.update(cls.table,entity,conditions)

  def delete(cls,conditions=None):
    '''
    Delete one or multi rows
    Parameter:
      conditions {dict | list<dict>} : the standard condition value ,like:
        {'field':'material_id','comparator':'=','value':'id2'} 
        [{'field':'material_id','comparator':'=','value':'id2'}]
    Return:
      {dict} : the standard sql output,like:
         {'code': 200, 'count': 1, 'sql': 'delete xxx'}
    '''
    return cls.SQL_EXECUTOR.delete(cls.table,conditions)

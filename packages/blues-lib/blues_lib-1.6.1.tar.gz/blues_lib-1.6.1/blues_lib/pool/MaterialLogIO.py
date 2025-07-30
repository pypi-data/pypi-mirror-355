import sys,os,re
from .BluesMaterial import BluesMaterial

class MaterialLogIO(BluesMaterial):
  '''
  Based on SQL, manage the input and output of materials.
  '''
  @classmethod
  def get_today_pubed_count(cls,platform,channel):
    '''
    Get today published count by channel
    '''
    conditions = [
      {'field':'DATE(pub_log_date)','comparator':'=','value':'CURDATE()','value_type':'function'},
      {'field':'pub_platform','comparator':'=','value':platform,'operator':'and'},
      {'field':'pub_channel','comparator':'=','value':channel,'operator':'and'},
      {'field':'pub_status','comparator':'=','value':'pubsuccess','operator':'and'},
    ]
    return cls.SQL_EXECUTOR.get(cls.MATERIAL_LOG_TABLE,'pub_m_id',conditions)

  @classmethod
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
    return cls.SQL_EXECUTOR.get(cls.MATERIAL_LOG_TABLE,fields,conditions,orders,pagination)

  @classmethod
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
    return cls.SQL_EXECUTOR.post(cls.MATERIAL_LOG_TABLE,fields,values)
  
  @classmethod
  def insert(cls,entities):
    '''
    Insert one more multi rows
    Parameter:
      entities {dict | list<dict>} : every dict contains field:value
    Return:
      {dict} : the standard sql output,like:
         {'code': 200, 'count': 1, 'sql': 'insert xxx'}
    '''
    return cls.SQL_EXECUTOR.insert(cls.MATERIAL_LOG_TABLE,entities)


  @classmethod 
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
    return cls.SQL_EXECUTOR.put(cls.MATERIAL_LOG_TABLE,fields,values,conditions)

  @classmethod 
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
    return cls.SQL_EXECUTOR.update(cls.MATERIAL_LOG_TABLE,entity,conditions)

  @classmethod
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
    return cls.SQL_EXECUTOR.delete(cls.MATERIAL_LOG_TABLE,conditions)

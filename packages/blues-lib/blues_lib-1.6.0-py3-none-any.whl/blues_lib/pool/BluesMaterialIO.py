from .BluesMaterial import BluesMaterial

class BluesMaterialIO(BluesMaterial):
  '''
  Based on SQL, manage the input and output of materials.
  '''

  @classmethod
  def exist(cls,brief):
    fields = ['material_id','material_title']
    conditions = [
      {
        'field':'material_id',
        'comparator':'=',
        'value':brief.get('material_id'),
      },
      {
        'operator':'or',
        'field':'material_title',
        'comparator':'like',
        'value':'%'+brief.get('material_title')+'%',
      } 
    ]
    result = cls.get(fields,conditions)
    return result['count']>0
  
  @classmethod
  def get(cls,fields=None,conditions=None,orders=None,pagination=None):
    '''
    Query rows
    Parameter:
      fields {list<str>} : the table fields 
      conditions {dict | list<dict>} : the standard condition value ,like:
        {'operator':'and','field':'material_id','comparator':'=','value':'id2'} 
        [{'operator':'and','field':'material_id','comparator':'=','value':'id2'}]
      orders {dict | list<dict>} : the standard order by dict, like:
        {'field':'material_status','sort':'asc'}
        [{'field':'material_status','sort':'asc'}]
      pagination {dict} : the standard pager dict, like:
        {'no':1,'size':10}
    Return:
      {dict} : the standard sql output,like:
         {'code': 200, 'count': 1, data: [{},{}],'sql': 'select xxx'}
    '''
    return cls.SQL_EXECUTOR.get(cls.MATERIAL_TABLE,fields,conditions,orders,pagination)

  @classmethod
  def random(cls):
    '''
    Get a random row
    '''
    # get all fields
    fields = '*' 
    conditions = [
      {'field':'material_body_text','comparator':'!=','value':''}, 
      {'field':'material_type','comparator':'=','value':'article'}, 
    ]
    # get the latest
    orders = [{
      'field':'rand()',
      'sort':''
    }]
    # get one row
    pagination = {
      'no':1,
      'size':1
    }
    return cls.get(fields,conditions,orders,pagination)

  @classmethod
  def latest(cls,count=1,material_type=''):
    '''
    Get the latest inserted row
    '''
    # get all fields
    fields = None 
    # only get the available row
    conditions = [{
      'field':'material_status',
      'comparator':'=',
      'value':'available'
    }]
    
    if material_type:
      conditions.append({
        'field':'material_type',
        'comparator':'=',
        'value':material_type
      })
      
    # get the latest
    orders = [{
      'field':'material_collect_date',
      'sort':'desc'
    }]
    # get one row
    pagination = {
      'no':1,
      'size':count
    }
    return cls.get(fields,conditions,orders,pagination)

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
    return cls.SQL_EXECUTOR.post(cls.MATERIAL_TABLE,fields,values)
  
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
    return cls.SQL_EXECUTOR.insert(cls.MATERIAL_TABLE,entities)


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
    return cls.SQL_EXECUTOR.put(cls.MATERIAL_TABLE,fields,values,conditions)

  @classmethod 
  def update(cls,entity,conditions=None):
    '''
    Update one or multi rows
    Parameter:
      entity {dict} : every dict contains field:value
      conditions {dict | list<dict>} : the standard condition value ,like:
        {'field':'material_id','comparator':'=','value':'id2'} 
        [{'field':'material_id','comparator':'=','value':'id2'}]
    Return:
      {dict} : the standard sql output,like:
         {'code': 200, 'count': 1, 'sql': 'update xxx'}
    '''
    return cls.SQL_EXECUTOR.update(cls.MATERIAL_TABLE,entity,conditions)

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
    return cls.SQL_EXECUTOR.delete(cls.MATERIAL_TABLE,conditions)

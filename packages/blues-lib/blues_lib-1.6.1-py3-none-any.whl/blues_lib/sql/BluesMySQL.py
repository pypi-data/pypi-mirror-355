import sys,os,re
import pymysql,traceback
from pymysql.converters import escape_string
sys.path.append(re.sub('blues_lib.*','blues_lib',os.path.realpath(__file__)))
from util.BluesConsole import BluesConsole 

# using the singleton to make sure using the only one cursor
class BluesMySQL():

  mysql = None
  
  @classmethod
  def get_instance(cls,account):
    if not cls.mysql:
      cls.mysql = BluesMySQL(account)
    return cls.mysql

  def __init__(self,account):
    '''
    @description : connect and execute sql
    @param {dict} account : MySQL account
    '''
    self.account = account
    self.__set_cursor()

  def __set_cursor(self):
    '''
    Create the connection cursor
    '''
    self.connector = self.__get_connector(self.account)
    self.cursor = self.connector.cursor() 

  def is_conn_lost(self):
    try:
      self.connector.ping(reconnect=True)
      return False
    except pymysql.Error as e:
      BluesConsole.error("MySQL lost connection %s" % e)
      return True
  
  def get(self,sql):
    # always fetch all rows, even only one row
    return self.__fetchall(sql)

  def post(self,sql,values=None):
    return self.__execute(sql,values)

  def put(self,sql,values=None):
    return self.__execute(sql,values)
  
  def delete(self,sql):
    return self.__execute(sql)

  def __get_connector(self,account):
    return  pymysql.connect(
      host=account['host'],
      user=account['user'],
      password=account['password'],
      database=account['database'],
      cursorclass=pymysql.cursors.DictCursor,  # 返回数组类型数据
      connect_timeout=90,  # 设置连接超时为 30 秒
      read_timeout=90,     # 设置查询超时为 60 秒
      write_timeout=160     # 设置写入超时为 60 秒
      )

  def __execute(self,sql,values=None):
    '''
    @description : insert/update/delete 
    @prams {str} sql : sql statement (with or without template)
    @params {tuple[]} values : multi real values
    @demo use placeholder
      - sql="insert into ics_test (name,age) values (%s,%s)"
      - execute: cursor.execute(sql,[('blues',18),('liu',12)])
    '''
    if self.mysql.is_conn_lost():
      self.__set_cursor()

    try:
      invoker_info = traceback.extract_stack()
      invoker = invoker_info[-2][2]
      
      # use executemany only when values is two-dimensional array
      if values and self.__is_series(values[0]):
        count=self.cursor.executemany(sql,self.__get_escape_rows(values))
      else:
        count=self.cursor.execute(sql,self.__get_escape_row(values))

      self.connector.commit()

      result = {
        'code':200,
        'count':count,
        'message':'success'
      }

      if invoker == 'get' or invoker == 'delete':
        result['sql'] = sql

      if invoker=='post':
        # if insert many rows, the row_id is the first inserted row's id (not the last inserted one)
        result['row_id'] = self.cursor.lastrowid

      return result

    except Exception as e:
      # sql error 2013 lost connection to MySQL server during query
      result = {
        'code':500,
        'message':e,
      }

      if invoker == 'get' or invoker == 'delete':
        result['sql'] = sql

      return result
  
  def __get_escape_row(self,row):
    '''
    Escape all string's Double quotation marks
    '''
    if not row:
      return row
    escape_row = []
    for value in row:
      if type(value) == str:
        escape_row.append(escape_string(value))
    return escape_row

  def __get_escape_rows(self,rows):
    if not rows:
      return rows
    escape_rows = []
    for row in rows:
      escape_rows.append(self.__get_escape_row(row))
    return escape_rows

  def __is_series(self,value):
    return isinstance(value, (list, tuple))

  def __fetchall(self,sql):
    '''
    @description Query rows of data
    @param {str} sql : Complete sql statement
    @returns {SQLResult} 
    '''
    if self.mysql.is_conn_lost():
      self.__set_cursor()

    try:
      self.cursor.execute(sql)
      rows=self.cursor.fetchall()
      # 立即提交，否则轮询会有缓存
      self.connector.commit()
      return {
        'code':200,
        'count':len(rows),
        'data':rows if rows else None, # 无数据返回空元组转为None
        'sql': sql,
      }
    except Exception as e:
      return {
        'code':500,
        'exception':e,
        'sql': sql,
      }




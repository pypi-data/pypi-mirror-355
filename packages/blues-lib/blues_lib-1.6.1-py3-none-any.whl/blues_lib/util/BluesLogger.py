import os,sys,re,logging,datetime
from .BluesFiler import BluesFiler 
from .BluesMailer import BluesMailer 

class BluesLogger():

  LOG_LEVELS = {
    'debug':logging.DEBUG,
    'info':logging.INFO, # will print all system info 
    'warning':logging.WARNING,
    'error':logging.ERROR,
  }

  DEFAULT_CONFIG = {
    'name':'system',
    'directory':'./log',
    'level':'info',
    'retention_days':7,
  }
  
  @classmethod
  def get_logger(cls,name=''):
    '''
    Get a named logger instance
    @param {str} name : the logger's name, recommand using the module name
    '''
    return logging.getLogger(name)

  @classmethod 
  def set_package_log(cls,name,level='info'):
    '''
    为某个模块设置日志层级，默认是warning，一般为了设置info调试
      - 必须在模块import前设置
    @param {str} name : 包名
      - 可通过遍历确认包名：for name in logging.root.manager.loggerDict:
    '''
    pkg_logger = logging.getLogger(name)  # 注意名称是 WDM
    pkg_logger.setLevel(cls.LOG_LEVELS[level])      # 允许输出 INFO 及以上级别
    # 可选：添加独立的控制台处理器（避免传播到根日志） - 经测试必须设置
    if not pkg_logger.handlers:
      handler = logging.StreamHandler()
      handler.setFormatter(logging.Formatter("%(name)s - %(message)s"))
      pkg_logger.addHandler(handler)

    # 禁止传播到父记录器（关键！避免被根日志过滤）
    pkg_logger.propagate = False

  def __init__(self,config={}):
    '''
    @description : set log config
    @param {str} config.directory : Directory for storing logs
    @param {str} config.name : log's topic
    @param {int} config.retention_days : Maximum number of days for storing logs
    @param {str} config.level : The lowest level of log output
      - enum: debug info warning error
    '''
    self.config = {**self.DEFAULT_CONFIG,**config}
    self.log_level  = self.LOG_LEVELS[self.config['level']]
    self.logger = self.__get_logger()
    # clear log history
    BluesFiler.removefiles(self.config['directory'],self.config['retention_days'])

  def __get_logger(self):

    logging.basicConfig(level=self.log_level)

    logger = logging.getLogger(self.config['name'])

    log_file = self.__get_log_file()
    formatter = self.__get_formatter()
    file_logger = logging.FileHandler(log_file,'a','utf-8')
    file_logger.setFormatter(formatter)

    logger.addHandler(file_logger)

    return logger

  def __get_formatter(self):
    split_line = '\n\n'+''.join(['-' for x in range(70)])
    formatter = split_line+'\n\n'+'%(levelname)s (%(name)s) %(asctime)s:\n%(filename)s (line:%(lineno)s) %(funcName)s:\n%(message)s'
    return logging.Formatter(formatter)
      
  def __get_log_file(self):
    today = datetime.datetime.now().strftime("%Y-%m-%d")
    log_name = '%s.log' % (today)
    log_file = '%s\\%s' % (self.config['directory'],log_name)
    # make sure the dir exist
    BluesFiler.makedirs(self.config['directory'])
    return log_file

  def write(self,payload):
    '''
    @description write log
    @param {LogPayload} payload
     - message : str
     - level : str
     - mail : MailPayload
    '''

    if not payload.get('message'):
      return 

    level = payload.get('level','info')
    log_method = getattr(self.logger,level) if hasattr(self.logger,level) else self.logger.info
    log_method(payload.get('message'))

    if payload.get('mail') and payload.get('mail').get('addressee'):
      mail_payload = self.__get_mail_payload(payload)
      BluesMailer.send(mail_payload)

  def __get_mail_payload(self,payload):
    return {
      'subject':'%s %s : %s' % (self.config['name'],payload.get('level'),payload.get('mail').get('subject')),
      'content':payload.get('message'),
      'addressee':payload.get('mail').get('addressee'), 
      'addressee_name':payload.get('mail').get('addressee_name'),
    }

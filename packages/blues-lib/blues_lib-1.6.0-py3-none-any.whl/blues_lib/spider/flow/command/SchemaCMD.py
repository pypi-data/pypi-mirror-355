import sys,os,re
sys.path.append(re.sub('blues_lib.*','blues_lib',os.path.realpath(__file__)))
from type.command.Command import Command
from schema.factory.LoginerSchemaFactory import LoginerSchemaFactory
from schema.factory.SpiderSchemaFactory import SpiderSchemaFactory

class SchemaCMD(Command):

  name = __name__

  # 暂不设置登录schema
  def execute(self):
    executor_stereotype = self._context['spider']['stereotype'].get('executor')
    executor_mode = executor_stereotype.get('basic').get('mode')
    executor_schema = SpiderSchemaFactory(executor_stereotype).create(executor_mode)
    if not executor_schema:
      raise Exception('[Spider] Failed to create the executor schema!')

    loginer_stereotype = self._context['spider']['stereotype'].get('loginer')
    loginer_schema = None
    if loginer_stereotype:
      loginer_mode = loginer_stereotype['basic'].get('mode')
      loginer_schema = LoginerSchemaFactory(loginer_stereotype).create(loginer_mode)

    self._context['spider']['schema'] = {
      'loginer':loginer_schema,
      'executor':executor_schema,
    }


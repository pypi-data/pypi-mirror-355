import sys,os,re
sys.path.append(re.sub('blues_lib.*','blues_lib',os.path.realpath(__file__)))
from type.command.Command import Command

class InputCMD(Command):

  name = __name__

  def execute(self):

    input = self._context.get('spider')
    if not input:
      raise Exception('[Spider] The param spider is missing!')

    stereotype = input.get('stereotype')
    if not stereotype:
      raise Exception('[Spider] The param spider.stereotype is missing!')

    executor_stereotype = stereotype.get('executor')
    if not executor_stereotype:
      raise Exception('[Spider] The param spider.stereotype.executor is missing!')


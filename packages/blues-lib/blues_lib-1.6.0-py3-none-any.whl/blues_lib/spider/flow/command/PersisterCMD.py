import sys,os,re
sys.path.append(re.sub('blues_lib.*','blues_lib',os.path.realpath(__file__)))
from type.command.Command import Command
from pool.BluesMaterialIO import BluesMaterialIO 

class PersisterCMD(Command):

  name = __name__

  def execute(self):
    executor_stereotype = self._context['spider']['stereotype'].get('executor')
    persistent = executor_stereotype.get('basic').get('persistent')
    if not persistent:
      return 

    items = self._context['spider'].get('items')

    response = BluesMaterialIO.insert(items)
    self._context['spider']['persister'] = response

    if response['code'] != 200:
      raise Exception('Failed to insert the items to the DB!')

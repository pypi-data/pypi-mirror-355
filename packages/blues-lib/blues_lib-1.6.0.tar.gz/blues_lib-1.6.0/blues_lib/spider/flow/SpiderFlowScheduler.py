import sys,os,re

from .SpiderFlow import SpiderFlow
sys.path.append(re.sub('blues_lib.*','blues_lib',os.path.realpath(__file__)))
from type.output.STDOut import STDOut

class SpiderFlowScheduler():

  def __init__(self,config):
    '''
    @description:
      - execute the spider flow for the given contexts
      - return the count of the items
    @params:
      - contexts {list<Dict>}: the contexts of the spiders, it's items is the spider context
      - count {int}: the count of the items - limit
    '''
    self._contexts = config.get('contexts',[])
    self._count = config.get('count',1)

  def execute(self):
    count = 0
    if not self._contexts:
      raise Exception('[Spider] The contexts is empty!')

    for context in self._contexts:
      flow = SpiderFlow(context)
      stdout = flow.execute()
      items = context['spider'].get('items')
      if stdout.code==200 and items:
        count += len(items)

      if count>=self._count:
        break

    if count==0:
      return STDOut(500,'[SpiderScheduler] No items found!')
    else:
      return STDOut(200,'[SpiderScheduler] Crawled [%s] items totally' % count)







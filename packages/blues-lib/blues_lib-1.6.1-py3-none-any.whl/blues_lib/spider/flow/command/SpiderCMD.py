import sys,os,re
sys.path.append(re.sub('blues_lib.*','blues_lib',os.path.realpath(__file__)))
from type.command.Command import Command
from spider.factory.SpiderFactory import SpiderFactory   

class SpiderCMD(Command):

  name = __name__

  def execute(self):
    browser = self._context['spider'].get('browser')

    schema = self._context['spider']['schema'].get('executor')
    # only material plan need this input
    brief = self._context['spider'].get('brief')

    artifact = schema.basic.get('artifact')

    request = {
      'browser':browser,
      'schema':schema,
      'brief':brief, # material plan need this input
    }

    spider = SpiderFactory(request).create(artifact)
    if not spider:
      raise Exception('[Spider] Failed to create a spider!')

    items = spider.spide()
    if not items:
      raise Exception('[Spider] Failed to crawl items!')

    self._context['spider']['items'] = items


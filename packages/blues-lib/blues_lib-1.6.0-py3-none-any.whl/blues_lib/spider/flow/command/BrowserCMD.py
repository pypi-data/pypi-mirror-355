import sys,os,re
sys.path.append(re.sub('blues_lib.*','blues_lib',os.path.realpath(__file__)))
from type.command.Command import Command
from sele.browser.BrowserFactory import BrowserFactory   

class BrowserCMD(Command):

  name = __name__

  def execute(self):

    executor_schema = self._context['spider']['schema'].get('executor')
    executable_path = executor_schema.browser.get('path')
    browser_mode = executor_schema.browser.get('mode') 

    loginer_schema = self._context['spider']['schema'].get('loginer')
    if loginer_schema:
      browser = BrowserFactory(browser_mode).create(executable_path=executable_path,loginer_schema=loginer_schema)
    else:
      browser = BrowserFactory(browser_mode).create(executable_path=executable_path)

    if not browser:
      raise Exception('[Spider] Failed to create the browser!')

    self._context['spider']['browser'] = browser

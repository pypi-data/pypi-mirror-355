
import sys,os,re
sys.path.append(re.sub('blues_lib.*','blues_lib',os.path.realpath(__file__)))
from sele.behavior.Behavior import Behavior
from sele.behavior.deco.BehaviorDeco import BehaviorDeco
from type.output.STDOut import STDOut

class Shot(Behavior):

  @BehaviorDeco()
  def resolve(self):
    if self.kind!='shot':
      return False 
    
    # if have no download file, will download to the default dir
    download_file = self.value
    if self.selector:
      # shot the element
      value = self.browser.element.shot.screenshot(self.selector,download_file,self.parent_selector,self.timeout)
    else:
      # shot the window
      value = self.browser.interactor.window.screenshot(download_file)

    return STDOut(data=value)


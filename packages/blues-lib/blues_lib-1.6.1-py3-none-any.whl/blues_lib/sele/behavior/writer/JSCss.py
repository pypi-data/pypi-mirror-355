import sys,os,re,time
sys.path.append(re.sub('blues_lib.*','blues_lib',os.path.realpath(__file__)))
from sele.behavior.Behavior import Behavior
from sele.behavior.deco.BehaviorDeco import BehaviorDeco
from type.output.STDOut import STDOut

class JSCss(Behavior):

  @BehaviorDeco()
  def resolve(self):

    if self.kind!='jscss':
      return False 
   
    # click to focus
    # value {dict} : as setter, css key-value
    # value {str} : as getter, return string
    value = self.browser.script.javascript.css(self.selector,self.value,self.parent_selector)

    return STDOut(data=value)

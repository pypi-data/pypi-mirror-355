import sys,os,re,time
sys.path.append(re.sub('blues_lib.*','blues_lib',os.path.realpath(__file__)))
from sele.behavior.Behavior import Behavior
from sele.behavior.deco.BehaviorDeco import BehaviorDeco
from type.output.STDOut import STDOut

class JSTextArea(Behavior):

  @BehaviorDeco()
  def resolve(self):

    if self.kind!='jstextarea':
      return False 
   
    LF_count = self.atom.get_LF_count()
    # click to focus
    # value {list<str>} : texts
    self.browser.script.javascript.write_para(self.selector,self.value,LF_count)

    return STDOut()

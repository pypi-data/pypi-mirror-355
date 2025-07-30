import sys,os,re
sys.path.append(re.sub('blues_lib.*','blues_lib',os.path.realpath(__file__)))
from sele.behavior.Behavior import Behavior
from sele.behavior.deco.BehaviorDeco import BehaviorDeco
from type.output.STDOut import STDOut

class JSClickable(Behavior):

  @BehaviorDeco()
  def resolve(self):
    '''
    Deal the atom
    Returns:
      {False} : the handler can't deal with the Atom
      {STDOut} : the result of handling
    '''
    if self.kind!='jsclickable':
      return False 

    selectors = [self.selector] if type(self.selector)==str else self.selector
    for selector in selectors:
      # only click one time
      if self.browser.waiter.querier.query(selector,self.parent_selector):
        self.browser.script.javascript.click(selector,self.parent_selector)
        break

    return STDOut()

import sys,os,re
from abc import ABC,abstractmethod
from .LoginerForm import LoginerForm
sys.path.append(re.sub('blues_lib.*','blues_lib',os.path.realpath(__file__)))
from sele.behavior.BehaviorChain import BehaviorChain

class AccountLoginerForm(LoginerForm,ABC):

  name = __name__

  def perform(self,browser):
    '''
    Implement the template method
    '''
    self.browser = browser
    self.prepare() 
    self.execute() 
    self.clean()
  
  def prepare(self):
    if self.schema.preparation:
      handler = BehaviorChain(self.browser,self.schema.preparation)
      handler.handle()

  def execute(self):
    if self.schema.execution:
      handler = BehaviorChain(self.browser,self.schema.execution)
      handler.handle()

  def clean(self):
    if self.schema.cleanup:
      handler = BehaviorChain(self.browser,self.schema.cleanup)
      handler.handle()

import sys,os,re
from functools import wraps
sys.path.append(re.sub('blues_lib.*','blues_lib',os.path.realpath(__file__)))
from util.BluesConsole import BluesConsole

class BehaviorDeco():
  '''
  Only used to the Acter class's resovle method
  '''

  def __init__(self,print_s_msg=False,print_f_msg=False):
    '''
    Create the decorator
    Parameter:
      print_s_msg {bool} : print the success message
      print_f_msg {bool} : print the failure message
    '''
    self.print_s_msg = print_s_msg
    self.print_f_msg = print_f_msg 

  def __call__(self,func):
    @wraps(func) 
    def wrapper(*args,**kwargs):

      # The first arg is the Acter class' self
      acter_self = args[0]

      # Use the inner msg to show more deal info
      template_values = (acter_self.kind,acter_self.selector,acter_self.__class__.__name__)
      s_msg = 'The atom {kind:%s,selector:%s} was dealt with [%s]' % template_values
      f_msg = 'The atom {kind:%s,selector:%s} can not be dealt with [%s]' % template_values
      
      # execute the wrappered func
      outcome = func(*args,**kwargs)
      
      # print success msg
      if outcome and self.print_s_msg:
        BluesConsole.success(s_msg)

      # print failure msg
      if not outcome and self.print_f_msg:
        BluesConsole.info(f_msg)
      
      # must return the wrappered func's value
      return outcome

    return wrapper


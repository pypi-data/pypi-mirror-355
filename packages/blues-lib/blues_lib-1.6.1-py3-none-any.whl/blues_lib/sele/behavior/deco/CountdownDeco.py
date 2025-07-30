import sys,os,re
from functools import wraps
sys.path.append(re.sub('blues_lib.*','blues_lib',os.path.realpath(__file__)))
from util.BluesDateTime import BluesDateTime

class CountdownDeco():
  '''
  Only used to the Acter class's resovle method
  '''

  def __init__(self,title='Count down',duration=1,position='after'):
    '''
    Count down 
    Parameter:
      title {str} : print title
      duration {int} : duration
      position {str} : after - count down after func; before - count down before func
    '''
    self.config = {
      'title':title,
      'duration':duration,
      'interval':1,
    }
    self.position = position

  def __call__(self,func):
    @wraps(func) 
    def wrapper(*args,**kwargs):
      
      if self.position == 'before':
        BluesDateTime.count_down(self.config)

      # execute the wrappered func
      outcome = func(*args,**kwargs)

      if self.position == 'after':
        BluesDateTime.count_down(self.config)
      
      # must return the wrappered func's value
      return outcome

    return wrapper


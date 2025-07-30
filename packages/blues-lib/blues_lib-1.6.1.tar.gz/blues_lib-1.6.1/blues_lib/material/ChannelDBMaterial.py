import sys,os,re
from .DBMaterial import DBMaterial
sys.path.append(re.sub('blues_lib.*','blues_lib',os.path.realpath(__file__)))
from pool.MaterialLogIO import MaterialLogIO
from util.BluesConsole import BluesConsole

class ChannelDBMaterial(DBMaterial):

  def __init__(self,platform,current_quota,query_condition):
    '''
    Parameters:
      platform {str} : the pub platform
      query_condition {dict} : the data query condition {'mode':'latest','count':None}
        - the count wll be calculated dynamic
      current_quota {dict}: want to fetch channel count {'events':1,'article':0}
    '''
    self.__platform = platform
    self.__current_quota = current_quota
    self.__query_condition = query_condition

  def get(self):

    # invoke the parent's get 
    materials = super().get(self.__query_condition)
    if not materials:
      return None

    channel_materials = {}
    avail_total = len(materials)
    actual_quota = {}
    allocated_count = 0
    
    # the db's remain avail count may less than the expected count
    for channel,count in self.__current_quota.items():
      if allocated_count>=avail_total:
        break

      channel_materials[channel] = materials[allocated_count:allocated_count+count]
      actual_quota[channel] = len(channel_materials[channel])
      allocated_count+=count
    
    BluesConsole.info('actual_quota: %s' % actual_quota)
    return channel_materials


import sys,os,re
sys.path.append(re.sub('blues_lib.*','blues_lib',os.path.realpath(__file__)))
from reporter.handler.ReporterHandler import ReporterHandler
from util.BluesDateTime import BluesDateTime
from util.BluesMailer import BluesMailer  
from deco.LogDeco import LogDeco

class PubNotifierHandler(ReporterHandler):

  kind = 'handler'

  @LogDeco()
  def resolve(self,rquest):
    '''
    Args:
      {dict} request : 
        - {dict} material 
    Returns {dict} response
      - {int} code
      - {str} message
    '''
    material = rquest.get('material')

    if not material:
      return {
        'code':404,
        'message':'No material to notify!',
      }

    mailer = BluesMailer.get_instance()
    
    subject = 'Succeeded' if material['material_status']=='pubsuccess' else 'Failed'
    subject += ' to publish: %s' % material['material_title']
    time = BluesDateTime.get_now() 
    para = '%s to %s as %s at %s' % (subject,material['material_pub_platform'],material['material_pub_channel'],time)
    content = mailer.get_html_body('ICPS published notification',para)
    payload={
      'subject':subject,
      'content':content,
      'images':None,
      'addressee':['langcai10@dingtalk.com'], # send to multi addressee
      'addressee_name':'BluesLiu',
    }
    response = mailer.send(payload)
    self.set_message(response)
    return response
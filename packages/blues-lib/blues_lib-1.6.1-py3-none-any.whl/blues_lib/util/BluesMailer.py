import smtplib,datetime
from email.mime.multipart import MIMEMultipart
from email.mime.text import MIMEText
from email.mime.image import MIMEImage
from email.message import EmailMessage
from email.header import Header
from .BluesDateTime import BluesDateTime

class BluesMailer():

  config = {
    # pick a smtp server
    'server' : 'smtp.qq.com',
    'port' : 465,
    # debug level: 0 - no message; 1 - many messages
    'debug_level' : 0, 
    # the sender's address
    'addresser' : '1121557826@qq.com',
    'addresser_name' : 'BluesLiu QQ',
    # the qq's auth code (not the account's login password)
    'addresser_pwd' : 'ryqokljshrrlifae',
  }

  __instance = None

  @classmethod
  def get_instance(cls):
    if not cls.__instance:
      cls.__instance = BluesMailer()
    return cls.__instance

  def __init__(self):
    self.connection = self.__get_connection()

  def __get_connection(self):
    connection = smtplib.SMTP_SSL(self.config['server'],self.config['port'])
    connection.set_debuglevel(self.config['debug_level'])
    connection.login(self.config['addresser'],self.config['addresser_pwd'])
    return connection

  def send(self,payload):
    '''
    @description : send the mail
    @param {MailPayload} payload : mail's required info
     - addressee ：list | str  ; required
     - addressee_name ：str , can't contains space
     - subject : str ; required
     - content : str 
    @returns {MailSentResult} : send result

    '''
    # the receiver's address
    if not payload.get('addressee'):
      return {
        'code':501,
        'message':'The addressee address is empty!'
      }
    
    if not payload.get('subject'):
      return {
        'code':502,
        'message':'The mail subject is empty!'
      }

    if not payload.get('content'):
      payload['content'] = payload['subject']
    
    try:
      message = self.__get_message(payload)
      self.connection.sendmail(self.config['addresser'],payload['addressee'],message)
      self.connection.quit()
    except Exception as e:
      return {
        'code':503,
        'message':'%s' % e
      }

    return {
      'code':200,
      'message':'Succeed to send mails.'
    }

  def get_title_with_time(self,title):
    return '%s - %s' % (title,BluesDateTime.get_time())

  def get_html_body(self,title,para,url='',url_text=''):
    now = BluesDateTime.get_now()
    link = ''
    if url and url_text:
      link = '''
        <p><a href="{}" style="font-size:16px;color:#07c;margin-top:1rem;">{}</a></p>
      '''.format(url,url_text)

    body = '''
    <div style="padding:0 10%;">
      <h1 style="margin:5rem 0 2rem 0;">{}</h1>
      <p style="color:gray;font-size:14px;">DateTime: {}</p>
      <p style="line-height:26px;font-size:16px;">{}</p>
      {}
    </div>
    '''.format(title,now,para,link)
    return body

  def __get_message(self,payload):
    message = MIMEMultipart()
    
    message['subject'] = payload['subject']
    # the last string must be from mail address
    from_with_nickname = '%s <%s>' % (self.config['addresser_name'],self.config['addresser']) 
    message['from'] = Header(from_with_nickname)

    if type(payload['addressee'])==str:
      message['to'] = Header(payload.get('addressee_name',payload['addressee']))
    else:
      message['to'] = Header(','.join(payload['addressee']))

    # support html document
    img_html = self.__get_img_html(message,payload.get('images'))
    message.attach(MIMEText(payload['content']+img_html, 'html'))
    return message.as_string()

  def __get_img_html(self,message,images):
    if not images:
      return ''
    
    html = ''
    i=0
    for image in images:
      with open(image, 'rb') as file:
        img = MIMEImage(file.read())
      i+=1
      cid = 'image%s' % i
      img.add_header('Content-ID', '<%s>' % cid)
      message.attach(img)
      html += '<p><img style="width:100%;" src="cid:{}"/></p>'.format(cid)
    return '<div style="padding:10px 10%;">{}</div>'.format(html)

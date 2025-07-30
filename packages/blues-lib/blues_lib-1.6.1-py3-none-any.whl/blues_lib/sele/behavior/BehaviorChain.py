# micro chain
from .MicroBehaviorChain import MicroBehaviorChain

# composite
from .composite.Array import Array  
from .composite.Map import Map  

# spider
from .spider.Brief import Brief
from .spider.Para import Para
from .spider.News import News

# releaser
from .releaser.RichText import RichText
from .releaser.ImageText import ImageText  

# decorator
from .deco.BehaviorDeco import BehaviorDeco

class BehaviorChain():

  def __init__(self,browser,atom):
    self.browser = browser
    self.atom = atom
    # set attrs for decorator's description
    self.category = self.atom.get_category()
    self.kind = self.atom.get_kind()
    if hasattr(self.atom,'get_selector'):
      self.selector = self.atom.get_selector()
    else:
      self.selector = None
  
  @BehaviorDeco(False,True)
  def handle(self):
    if not self.atom:
      return False
    '''
    Deal the atom by the event chain
    '''
    handler = self.__get_chain()
    return handler.handle()

  def __get_chain(self):
    '''
    Create the  chain
    Returns:
      {} : the first atom
    '''
    # micro chain
    micro_chain = MicroBehaviorChain(self.browser,self.atom)

    # composite
    array = Array(self.browser,self.atom)
    map = Map(self.browser,self.atom)

    # spider
    brief = Brief(self.browser,self.atom)
    para = Para(self.browser,self.atom)
    news = News(self.browser,self.atom)

    # releaser
    richtext = RichText(self.browser,self.atom)
    imagetext = ImageText(self.browser,self.atom)

    micro_chain.set_next(array) \
      .set_next(map) \
      .set_next(brief) \
      .set_next(para) \
      .set_next(news) \
      .set_next(richtext) \
      .set_next(imagetext) 
    
    return micro_chain

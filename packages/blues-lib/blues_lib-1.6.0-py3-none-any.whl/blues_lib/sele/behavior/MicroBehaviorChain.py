from sele.behavior.Behavior import Behavior

# plain
from .plain.Pause import Pause  

# writer
from .writer.Choice import Choice  
from .writer.Select import Select  
from .writer.InputChar import InputChar  
from .writer.Input import Input  
from .writer.TextArea import TextArea  
from .writer.JSCss import JSCss  
from .writer.JSText import JSText  
from .writer.JSTextArea import JSTextArea  
from .writer.File import File  

# event
from .event.Clickable import Clickable  
from .event.JSClickable import JSClickable  
from .event.Hover import Hover  
from .event.Rollin import Rollin  
from .event.Frame import Frame  
from .event.Popup import Popup  

# reader
from .reader.Attr import Attr  
from .reader.Value import Value  
from .reader.Text import Text  
from .reader.Css import Css  
from .reader.Shot import Shot  

# decorator
from .deco.BehaviorDeco import BehaviorDeco

class MicroBehaviorChain(Behavior):
  '''
  Basic behavior chain, it's a behavior too
  '''
  
  @BehaviorDeco(False,True)
  def resolve(self):
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
    # writer
    choice = Choice(self.browser,self.atom)
    select = Select(self.browser,self.atom)
    inputchar = InputChar(self.browser,self.atom)
    input = Input(self.browser,self.atom)
    textarea = TextArea(self.browser,self.atom)
    jscss = JSCss(self.browser,self.atom)
    jstext = JSText(self.browser,self.atom)
    jstextarea = JSTextArea(self.browser,self.atom)
    file = File(self.browser,self.atom)

    # event
    clickable = Clickable(self.browser,self.atom)
    jsclickable = JSClickable(self.browser,self.atom)
    hover = Hover(self.browser,self.atom)
    rollin = Rollin(self.browser,self.atom)
    frame = Frame(self.browser,self.atom)
    popup = Popup(self.browser,self.atom)

    # reader
    attr = Attr(self.browser,self.atom)
    value = Value(self.browser,self.atom)
    text = Text(self.browser,self.atom)
    css = Css(self.browser,self.atom)
    shot = Shot(self.browser,self.atom)

    # plain
    pause = Pause(self.browser,self.atom)

    choice.set_next(select) \
      .set_next(inputchar) \
      .set_next(input) \
      .set_next(textarea) \
      .set_next(jscss) \
      .set_next(jstext) \
      .set_next(jstextarea) \
      .set_next(file) \
      .set_next(clickable) \
      .set_next(jsclickable) \
      .set_next(hover) \
      .set_next(rollin) \
      .set_next(frame) \
      .set_next(popup) \
      .set_next(attr) \
      .set_next(value) \
      .set_next(text) \
      .set_next(css) \
      .set_next(shot) \
      .set_next(pause) 

    return choice

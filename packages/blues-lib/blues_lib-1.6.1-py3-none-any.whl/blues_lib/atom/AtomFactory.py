
# plain atoms
from .plain.DataAtom import DataAtom
from .plain.PauseAtom import PauseAtom
from .plain.RegexpAtom import RegexpAtom
from .plain.URLAtom import URLAtom

# event atoms
from .event.ElementAtom import ElementAtom
from .event.ClickableAtom import ClickableAtom
from .event.JSClickableAtom import JSClickableAtom
from .event.HoverAtom import HoverAtom
from .event.FrameAtom import FrameAtom
from .event.RollinAtom import RollinAtom
from .event.PopupAtom import PopupAtom

# writer atoms
from .writer.InputAtom import InputAtom
from .writer.InputCharAtom import InputCharAtom
from .writer.TextAreaAtom import TextAreaAtom
from .writer.JSCssAtom import JSCssAtom
from .writer.JSTextAtom import JSTextAtom
from .writer.JSTextAreaAtom import JSTextAreaAtom
from .writer.FileAtom import FileAtom
from .writer.ChoiceAtom import ChoiceAtom
from .writer.SelectAtom import SelectAtom

# releaser
from .releaser.RichTextAtom import RichTextAtom
from .releaser.ImageTextAtom import ImageTextAtom

# reader atoms
from .reader.AttrAtom import AttrAtom
from .reader.TextAtom import TextAtom
from .reader.ValueAtom import ValueAtom
from .reader.CssAtom import CssAtom
from .reader.ShotAtom import ShotAtom

# composite
from .composite.ArrayAtom import ArrayAtom
from .composite.MapAtom import MapAtom

# spider atoms
from .spider.BriefAtom import BriefAtom
from .spider.NewsAtom import NewsAtom
from .spider.ParaAtom import ParaAtom

class AtomFactory():

  # create plain Atoms
  def create_data(self,title,value):
    return DataAtom(title,value)

  def create_pause(self,title,value=5):
    return PauseAtom(title,value)

  def create_regexp(self,title,value):
    return RegexpAtom(title,value)

  def create_url(self,title,value):
    return URLAtom(title,value)

  # create event Atoms
  def create_element(self,title,selector,value=None,parent_selector=None,timeout=5,selector_template=None):
    return ElementAtom(title,selector,value,parent_selector,timeout,selector_template)

  def create_rollin(self,title,selector,value=None,parent_selector=None,timeout=5,selector_template=None):
    return RollinAtom(title,selector,value,parent_selector,timeout,selector_template)

  def create_popup(self,title,selector,value=None,parent_selector=None,timeout=5,selector_template=None):
    return PopupAtom(title,selector,value,parent_selector,timeout,selector_template)

  def create_clickable(self,title,selector,value=None,parent_selector=None,timeout=5,selector_template=None):
    return ClickableAtom(title,selector,value,parent_selector,timeout,selector_template)

  def create_jsclickable(self,title,selector,value=None,parent_selector=None,timeout=5,selector_template=None):
    return JSClickableAtom(title,selector,value,parent_selector,timeout,selector_template)

  def create_hover(self,title,selector,value=None,parent_selector=None,timeout=5,selector_template=None):
    return HoverAtom(title,selector,value,parent_selector,timeout,selector_template)

  def create_frame(self,title,selector,value='in',parent_selector=None,timeout=5,selector_template=None):
    return FrameAtom(title,selector,value,parent_selector,timeout,selector_template)
  
  # create writer Atoms
  def create_inputchar(self,title,selector,value=None,interval=1,mode='replace',parent_selector=None,timeout=5,selector_template=None):
    return InputCharAtom(title,selector,value,interval,mode,parent_selector,timeout,selector_template)

  def create_input(self,title,selector,value=None,parent_selector=None,timeout=5,selector_template=None):
    return InputAtom(title,selector,value,parent_selector,timeout,selector_template)

  def create_textarea(self,title,selector,value=None,LF_count=1,parent_selector=None,timeout=5,selector_template=None):
    return TextAreaAtom(title,selector,value,LF_count,parent_selector,timeout,selector_template)

  def create_jscss(self,title,selector,value=None,parent_selector=None,timeout=5,selector_template=None):
    return JSCssAtom(title,selector,value,parent_selector,timeout,selector_template)

  def create_jstext(self,title,selector,value=None,parent_selector=None,timeout=5,selector_template=None):
    return JSTextAtom(title,selector,value,parent_selector,timeout,selector_template)

  def create_jstextarea(self,title,selector,value=None,LF_count=1,parent_selector=None,timeout=5,selector_template=None):
    return JSTextAreaAtom(title,selector,value,LF_count,parent_selector,timeout,selector_template)

  def create_file(self,title,selector,value=None,wait_time=5,parent_selector=None,timeout=5,selector_template=None):
    return FileAtom(title,selector,value,wait_time,parent_selector,timeout,selector_template)

  def create_select(self,title,selector,value=True,parent_selector=None,timeout=5,selector_template=None):
    return SelectAtom(title,selector,value,parent_selector,timeout,selector_template)

  def create_choice(self,title,selector,value=True,parent_selector=None,timeout=5,selector_template=None):
    return ChoiceAtom(title,selector,value,parent_selector,timeout,selector_template)
  
  # releaser atoms
  def create_richtext(self,title,selector='',value=None,selector_template=None):
    return RichTextAtom(title,selector,value,selector_template)

  def create_imagetext(self,title,selector='',value=None):
    return ImageTextAtom(title,selector,value)

  # reader atoms
  def create_text(self,title,selector,value=None,parent_selector=None,timeout=5,selector_template=None):
    return TextAtom(title,selector,value,parent_selector,timeout,selector_template)

  def create_value(self,title,selector,value=None,parent_selector=None,timeout=5,selector_template=None):
    return ValueAtom(title,selector,value,parent_selector,timeout,selector_template)

  def create_attr(self,title,selector,value=None,parent_selector=None,timeout=5,selector_template=None):
    return AttrAtom(title,selector,value,parent_selector,timeout,selector_template)

  def create_shot(self,title,selector=None,value=None,parent_selector=None,timeout=5,selector_template=None):
    return ShotAtom(title,selector,value,parent_selector,timeout,selector_template)

  def create_css(self,title,selector,value=None,parent_selector=None,timeout=5,selector_template=None):
    return CssAtom(title,selector,value,parent_selector,timeout,selector_template)
  
  # composite atoms
  def create_array(self,title,value=None,pause=1):
    return ArrayAtom(title,value,pause)

  def create_map(self,title,value=None,pause=1):
    return MapAtom(title,value,pause)

  # spider atoms
  def create_para(self,title,selector,value):
    return ParaAtom(title,selector,value)

  def create_brief(self,title,selector,value):
    return BriefAtom(title,selector,value)

  def create_news(self,title,selector,value):
    return NewsAtom(title,selector,value)

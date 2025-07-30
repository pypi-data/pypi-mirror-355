from .BehaviorChain import BehaviorChain   

class FormBehavior():
  '''
  Deal a form submission behaviors
  '''

  def __init__(self,browser,array_atom,popup_atom=None):
    '''
    Parameter:
      browser {BluesBrowser}
      array_atom {ArrayAtom} : the main form fill and submit atoms
      popup_atom {PopupAtom} : the popup need to be removed
    '''
    self.__browser = browser
    self.__array_atom = array_atom
    self.__popup_atom = popup_atom

  def handle(self):
    '''
    Write fields in any channel's form
    Driver by the meata data
    '''
    self.__popoff()
    handler = BehaviorChain(self.__browser,self.__array_atom) 
    return handler.handle()

  def __popoff(self):
    if not self.__popup_atom:
      return

    handler = BehaviorChain(self.__browser,self.__popup_atom) 
    handler.handle()

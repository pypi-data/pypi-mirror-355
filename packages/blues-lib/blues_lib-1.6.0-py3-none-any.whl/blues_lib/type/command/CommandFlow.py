import sys,os,re
from abc import ABC,abstractmethod
sys.path.append(re.sub('blues_lib.*','blues_lib',os.path.realpath(__file__)))
from type.command.Command import Command
from type.output.STDOut import STDOut

class CommandFlow(ABC):
  
  def __init__(self,context:dict):
    self._commands:list[Command] = []
    self._context:dict = context

  def get_commands(self):
    return self._commands
    
  def get_context(self):
    return self._context
    
  def add(self,command:Command):
    # add one command
    self._commands.append(command)
    
  def execute(self):

    self.load()
    if not self._commands:
      return STDOut(500,'No commands to execute!')

    try:
      for command in self._commands:
        command.execute()
      return STDOut(200,'Succeed to execute the flow.')
    except Exception as e:
      return STDOut(500,str(e))

  @abstractmethod
  def load(self)->None:
    # Set the command list before execution
    pass

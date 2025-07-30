import sys,os,re
sys.path.append(re.sub('blues_lib.*','blues_lib',os.path.realpath(__file__)))
from flow.sap.SAPFlow import SAPFlow
from mock.stereotype.MockStereotype import MockStereotype
from mock.prompt.MockPrompt import MockPrompt

class MockSAPFlow(SAPFlow):
  def __init__(self,spdier,ai,publisher):
    context = {
      'spider':self._get_context_node(spdier),
      'ai':self._get_context_node(ai),
      'publisher':self._get_context_node(publisher),
    }
    super().__init__(context)

  def _get_context_node(self,node_config:dict):
    if node_config.get('contexts'):
      return node_config

    stereotype = {}
    for key in node_config:
      config = node_config[key]
      stereotype[key] = self._get_stereotype(config) if config else None

    return {
      'stereotype':stereotype,
    }

  def _get_stereotype(self,config):
    
    root = config.get('root')
    path = config.get('path')
    file = config.get('file')
    if not root or not path or not file:
      return config

    if root == 'prompt':
      return MockPrompt.get(*path).get(file)
    elif root == 'stereotype':
      return MockStereotype.get(*path).get(file)
    else:
      return None

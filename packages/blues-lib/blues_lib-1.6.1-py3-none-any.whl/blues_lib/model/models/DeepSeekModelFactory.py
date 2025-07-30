import sys,os,re
from .ModelFactory import ModelFactory
sys.path.append(re.sub('test.*','blues_lib',os.path.realpath(__file__)))
from model.AIQAModel import AIQAModel
from schema.ai.deepseek.DeepSeekSchemaFactory import DeepSeekSchemaFactory

class DeepSeekModelFactory(ModelFactory):

  PLATFORM = 'deepseek'

  def __init__(self):
    self.schema_factory = DeepSeekSchemaFactory()

  def create_qa(self,material):
    schema = self.schema_factory.create_qa()
    return AIQAModel(schema,material).first()

  def create_qas(self,materials):
    schema = self.schema_factory.create_qa()
    return AIQAModel(schema,materials).get()

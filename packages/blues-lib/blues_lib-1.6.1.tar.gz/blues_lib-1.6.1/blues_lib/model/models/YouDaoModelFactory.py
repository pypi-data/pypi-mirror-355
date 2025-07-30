import sys,os,re
from .ModelFactory import ModelFactory
sys.path.append(re.sub('test.*','blues_lib',os.path.realpath(__file__)))
from model.AIQAModel import AIQAModel
from schema.ai.youdao.YouDaoSchemaFactory import YouDaoSchemaFactory

class YouDaoModelFactory(ModelFactory):

  PLATFORM = 'youdao'
  def __init__(self):
    self.schema_factory = YouDaoSchemaFactory()

  def create_translator(self,material):
    schema = self.schema_factory.create_translator()
    return AIQAModel(schema,material).first()

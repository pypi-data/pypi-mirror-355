import sys,os,re
from .ModelFactory import ModelFactory
sys.path.append(re.sub('test.*','blues_lib',os.path.realpath(__file__)))
from model.AIQAModel import AIQAModel
from schema.ai.doubao.DouBaoSchemaFactory import DouBaoSchemaFactory

class DouBaoModelFactory(ModelFactory):

  PLATFORM = 'doubao'
  def __init__(self):
    self.schema_factory = DouBaoSchemaFactory()

  def create_qa(self,material):
    schema = self.schema_factory.create_qa()
    return AIQAModel(schema,material).first()

  def create_qas(self,materials):
    schema = self.schema_factory.create_qa()
    return AIQAModel(schema,materials).get()

  def create_img_gen(self,material):
    schema = self.schema_factory.create_img_gen()
    return AIQAModel(schema,material).first()



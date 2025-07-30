import sys,os,re
sys.path.append(re.sub('blues_lib.*','blues_lib',os.path.realpath(__file__)))
from schema.factory.SchemaFactory import SchemaFactory
from schema.ai.writer.WriterAISchema import WriterAISchema

class AISchemaFactory(SchemaFactory):

  name = __name__

  def create_writer(self):
    if not self._is_legal_meta(WriterAISchema):
      return None

    meta = self._get_atom_meta()
    return WriterAISchema(meta)

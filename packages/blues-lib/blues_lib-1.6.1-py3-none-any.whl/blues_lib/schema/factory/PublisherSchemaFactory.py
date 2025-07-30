import sys,os,re
sys.path.append(re.sub('blues_lib.*','blues_lib',os.path.realpath(__file__)))
from schema.factory.SchemaFactory import SchemaFactory
from schema.publisher.article.ArticlePublisherSchema import ArticlePublisherSchema

class PublisherSchemaFactory(SchemaFactory):

  name = __name__

  def create_article(self):
    if not self._is_legal_meta(ArticlePublisherSchema):
      return None

    meta = self._get_atom_meta()
    return ArticlePublisherSchema(meta)

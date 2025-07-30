import sys,os,re
sys.path.append(re.sub('blues_lib.*','blues_lib',os.path.realpath(__file__)))
from schema.factory.SchemaFactory import SchemaFactory
from schema.spider.article.ArticleSpiderSchema import ArticleSpiderSchema
from schema.spider.gallery.GallerySpiderSchema import GallerySpiderSchema

class SpiderSchemaFactory(SchemaFactory):

  name = __name__

  def create_article(self):
    if not self._is_legal_meta(ArticleSpiderSchema):
      return None

    meta = self._get_atom_meta()
    return ArticleSpiderSchema(meta)

  def create_gallery(self):
    if not self._is_legal_meta(GallerySpiderSchema):
      return None

    meta = self._get_atom_meta()
    return GallerySpiderSchema(meta)
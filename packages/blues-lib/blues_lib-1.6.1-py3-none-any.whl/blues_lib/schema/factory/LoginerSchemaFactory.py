import sys,os,re
sys.path.append(re.sub('blues_lib.*','blues_lib',os.path.realpath(__file__)))
from schema.factory.SchemaFactory import SchemaFactory
from schema.loginer.account.AccountLoginerSchema import AccountLoginerSchema
from schema.loginer.mac.MACLoginerSchema import MACLoginerSchema
from schema.loginer.qrc.QRCodeLoginerSchema import QRCodeLoginerSchema

class LoginerSchemaFactory(SchemaFactory):

  name = __name__

  def create_account(self):
    if not self._is_legal_meta(AccountLoginerSchema):
      return None

    meta = self._get_atom_meta()
    return AccountLoginerSchema(meta)

  def create_mac(self):
    if not self._is_legal_meta(MACLoginerSchema):
      return None

    meta = self._get_atom_meta()
    return MACLoginerSchema(meta)

  def create_qrc(self):
    if not self._is_legal_meta(QRCodeLoginerSchema):
      return None

    meta = self._get_atom_meta()
    return QRCodeLoginerSchema(meta)

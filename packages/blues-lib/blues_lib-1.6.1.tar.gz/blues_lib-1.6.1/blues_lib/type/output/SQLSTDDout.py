from STDOut import STDOut

class SQLSTDOut(STDOut):
  def __init__(self,code=200,message='success',data=None,count=0,sql=''):
    super().__init__(code,message,data)
    self.count = count
    self.sql = sql


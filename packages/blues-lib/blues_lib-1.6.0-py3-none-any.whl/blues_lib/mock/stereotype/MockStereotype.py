import sys,os,re
sys.path.append(re.sub('blues_lib.*','blues_lib',os.path.realpath(__file__)))
from mock.MockQuery import MockQuery

class MockStereotype(MockQuery):

  @classmethod
  def _get_base_dir(cls) -> str:
    """覆盖父类获得正确的目录 - 获取基准目录路径（当前文件所在目录）"""
    return os.path.dirname(os.path.abspath(__file__))
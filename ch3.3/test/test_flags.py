import sys
import pathlib

import pytest

sys.path.append(str(pathlib.Path.cwd().parent) + '/src')
from flags import Flags


def test_ex():
  e1 = Flags.A | Flags.C
  e2 = Flags.B | Flags.C
  
  assert (e1 | e2) == Flags.ABC
  assert (e1 & e2) == Flags.C
  #assert (e1 - e2) == Flags.A
  assert e2 != Flags.A
  

if __name__ == '__main__':
  pytest.main()


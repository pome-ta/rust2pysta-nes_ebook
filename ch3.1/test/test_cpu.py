import pytest

import sys
import pathlib
sys.path.append(str(pathlib.Path.cwd().parent))

from src.cpu import CPU


def test_0xa9_lda_immidiate_load_data():
  cpu = CPU()
  cpu.interpret([0xa9, 0x05, 0x00])
  assert cpu.register_a == 5
  assert cpu.status & 0b0000_0010 == 0
  assert cpu.status & 0b1000_0000 == 0


def test_0xa9_lda_zero_flag():
  cpu = CPU()
  cpu.interpret([0xa9, 0x00, 0x00])
  assert cpu.status & 0b0000_0010 == 0b10


def test_0xa9_lda_negative_flag():
  cpu = CPU()
  cpu.interpret([0xa9, 0xff, 0x00])
  assert cpu.status & 0b1000_0000 == 0b1000_0000


def test_0xaa_tax_move_a_to_x():
  cpu = CPU()
  cpu.register_a = 10
  cpu.interpret([0xaa, 0x00])

  assert cpu.register_x == 10


def test_5_ops_working_together():
  cpu = CPU()
  cpu.interpret([0xa9, 0xc0, 0xaa, 0xe8, 0x00])
  assert cpu.register_x == 0xc1


def test_inx_overflow():
  cpu = CPU()
  cpu.register_x = 0xff
  cpu.interpret([0xe8, 0xe8, 0x00])
  assert cpu.register_x == 1


pytest.main()


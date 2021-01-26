import sys
import pathlib

import pytest

sys.path.append(str(pathlib.Path.cwd().parent) + '/src')
from cpu import CPU


def test_0xa9_lda_immidiate_load_data():
  cpu = CPU()
  cpu.load_and_run([0xa9, 0x05, 0x00])
  assert cpu.register_a == 5
  assert cpu.status.bits & 0b0000_0010 == 0b00
  assert cpu.status.bits & 0b1000_0000 == 0


def test_0xaa_tax_move_a_to_x():
  cpu = CPU()
  cpu.register_a = 10
  cpu.load_and_run([0xaa, 0x00])
  assert cpu.register_x == 10


def test_5_ops_working_together():
  cpu = CPU()
  cpu.load_and_run([0xa9, 0xc0, 0xaa, 0xe8, 0x00])
  assert cpu.register_x == 0xc1


def test_inx_overflow():
  cpu = CPU()
  cpu.register_x = 0xff
  cpu.load_and_run([0xe8, 0xe8, 0x00])
  assert cpu.register_x == 1


def test_lda_from_memory():
  cpu = CPU()
  cpu.mem_write(0x10, 0x55)
  cpu.load_and_run([0xa5, 0x10, 0x00])
  assert cpu.register_a == 0x55


if __name__ == '__main__':
  pytest.main()


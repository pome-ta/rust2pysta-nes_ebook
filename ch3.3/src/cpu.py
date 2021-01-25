from typing import NamedTuple
from enum import IntFlag
import copy


class CpuFlags(IntFlag):
  """  Status Register (P)
      http://wiki.nesdev.com/w/index.php/Status_flags

    7 6 5 4 3 2 1 0
    N V _ B D I Z C
    | |   | | | | +--- Carry Flag
    | |   | | | +----- Zero Flag
    | |   | | +------- Interrupt Disable
    | |   | +--------- Decimal Mode (not used on NES)
    | |   +----------- Break Command
    | +--------------- Overflow Flag
    +----------------- Negative Flag
    """

  CARRY = 0b0000_0001
  ZERO = 0b0000_0010
  INTERRUPT_DISABLE = 0b0000_0100
  DECIMAL_MODE = 0b0000_1000
  BREAK = 0b0001_0000
  BREAK2 = 0b0010_0000
  OVERFLOW = 0b0100_0000
  NEGATIV = 0b1000_0000
  NULL = 0

# fixme: XXX... CpuFlags
class BitFlags:
  def __new__(cls):
    self = super().__new__(cls)
    self.bits = CpuFlags.NULL
    return self

  @classmethod
  def from_bits_truncate(cls, byte: 'u8') -> 'BitFlags':
    obj = cls()
    obj.bits |= byte
    return obj

  def contains(self, byte: 'u8') -> bool:
    return (self.bits & byte) == byte

  def insert(self, byte: 'u8'):
    self.bits |= byte

  def remove(self, byte: 'u8'):
    self.bits &= -(byte + 1)

  def set(self, byte: 'u8', value: bool):
    if value:
      self.insert(byte)
    else:
      self.remove(byte)

  def clone(self):
    return copy.copy(self)


STACK: 'u16' = 0x0100
STACK_RESET: 'u8' = 0xfd


class _AddressingMode(NamedTuple):
  Immediate: int = 1
  ZeroPage: int = 2
  ZeroPage_X: int = 3
  ZeroPage_Y: int = 4
  Absolute: int = 5
  Absolute_X: int = 6
  Absolute_Y: int = 7
  Indirect_X: int = 8
  Indirect_Y: int = 9
  NoneAddressing: int = 10


AddressingMode = _AddressingMode()
import opcodes


class CPU:
  def __init__(self):
    self.register_a: 'u8' = 0
    self.register_x: 'u8' = 0
    self.register_y: 'u8' = 0
    self.stack_pointer: 'u8' = STACK_RESET
    self.program_counter: 'u16' = 0
    self.status = BitFlags.from_bits_truncate(0b100100)
    self.memory = [None] * 0xFFFF

  def mem_read(self, addr: 'u16') -> 'u8':
    return self.memory[addr]

  def mem_write(self, addr: 'u16', data: 'u8'):
    self.memory[addr] = data

  def mem_read_u16(self, pos: 'u16') -> 'u16':
    lo = self.mem_read(pos)
    hi = self.mem_read(pos + 1)
    # test: _ = (hi << 8) | (lo)
    return (hi << 8) | (lo)

  def mem_write_u16(self, pos: 'u16', data: 'u16'):
    hi = (data >> 8)
    lo = (data & 0xff)
    self.mem_write(pos, lo)
    self.mem_write(pos + 1, hi)

  def get_operand_address(self, mode: '&AddressingMode') -> 'u16':
    # --- 1 -> Immediate
    if mode == 1:
      return self.program_counter

    # --- 2 -> ZeroPage
    elif mode == 2:
      return self.mem_read(self.program_counter)

    # --- 5 -> Absolute
    elif mode == 5:
      return self.mem_read_u16(self.program_counter)

    # --- 3 -> ZeroPage_X
    elif mode == 3:
      pos = self.mem_read(self.program_counter)
      addr = pos + self.register_x
      # todo: Overflow -> wrapping_add
      if addr > 0b1111_1111:
        addr = addr - (0b1111_1111 + 1)
      return addr

    # --- 4 -> ZeroPage_Y
    elif mode == 4:
      pos = self.mem_read(self.program_counter)
      addr = pos + self.register_y
      # todo: Overflow -> wrapping_add
      if addr > 0b1111_1111:
        addr = addr - (0b1111_1111 + 1)
      return addr

    # --- 6 -> Absolute_X
    elif mode == 6:
      base = self.mem_read_u16(self.program_counter)
      addr = base + self.register_x
      # todo: Overflow -> wrapping_add
      if addr > 0b1111_1111:
        addr = addr - (0b1111_1111 + 1)
      return addr

    # --- 7 -> Absolute_Y
    elif mode == 7:
      base = self.mem_read_u16(self.program_counter)
      addr = base + self.register_y
      # todo: Overflow -> wrapping_add
      if addr > 0b1111_1111:
        addr = addr - (0b1111_1111 + 1)
      return addr

    # --- 8 -> Indirect_X
    elif mode == 8:
      base = self.mem_read(self.program_counter)
      ptr = base + self.register_x
      # todo: Overflow -> wrapping_add
      if ptr > 0b1111_1111:
        ptr = ptr - (0b1111_1111 + 1)
      lo = self.mem_read(ptr)
      ptr += 1
      # todo: Overflow -> wrapping_add
      if ptr > 0b1111_1111:
        ptr = ptr - (0b1111_1111 + 1)
      hi = self.mem_read(ptr)
      return (hi) << 8 | (lo)

    # --- 9 -> Indirect_Y
    elif mode == 9:
      base = self.mem_read(self.program_counter)
      lo = self.mem_read(base)
      base += 1
      # todo: Overflow -> wrapping_add
      if base > 0b1111_1111:
        base = base - (0b1111_1111 + 1)
      hi = self.mem_read(base)
      deref_base = (hi) << 8 | (lo)
      deref = deref_base + self.register_y
      # todo: Overflow -> wrapping_add
      if deref > 0b1111_1111:
        deref = deref - (0b1111_1111 + 1)
      return deref

    # --- 10 -> NoneAddressing
    elif mode == 10:
      print(f'mode {mode} is not supported')

  def ldy(self, mode: '&AddressingMode'):
    addr = self.get_operand_address(mode)
    data = self.mem_read(addr)
    self.register_y = data
    self.update_zero_and_negative_flags(self.register_y)

  def ldx(self, mode: '&AddressingMode'):
    addr = self.get_operand_address(mode)
    data = self.mem_read(addr)
    self.register_x = data
    self.update_zero_and_negative_flags(self.register_x)

  def lda(self, mode: '&AddressingMode'):
    addr = self.get_operand_address(mode)
    value = self.mem_read(addr)
    self.set_register_a(value)

  def sta(self, mode: '&AddressingMode'):
    addr = self.get_operand_address(mode)
    self.mem_write(addr, self.register_a)

  def set_register_a(self, value: 'u8'):
    self.register_a = value
    self.update_zero_and_negative_flags(self.register_a)

  # fixme: 予約語 `and` -> `_and`
  def _and(self, mode: '&AddressingMode'):
    addr = self.get_operand_address(mode)
    data = self.mem_read(addr)
    self.set_register_a(data & self.register_a)

  def eor(self, mode: '&AddressingMode'):
    addr = self.get_operand_address(mode)
    data = self.mem_read(addr)
    self.set_register_a(data ^ self.register_a)

  def ora(self, mode: '&AddressingMode'):
    addr = self.get_operand_address(mode)
    data = self.mem_read(addr)
    self.set_register_a(data | self.register_a)

  def tax(self):
    self.register_x = self.register_a
    self.update_zero_and_negative_flags(self.register_x)

  def update_zero_and_negative_flags(self, result: 'u8'):
    # fixme: bitflags
    if result == 0:
      self.status = self.status | 0b0000_0010
    else:
      self.status = self.status & 0b1111_1101

    if result & 0b1000_0000 != 0:
      self.status = self.status | 0b1000_0000
    else:
      self.status = self.status & 0b0111_1111

  def inx(self):
    self.register_x += 1
    # todo: Overflow -> wrapping_add
    if self.register_x > 0b1111_1111:
      self.register_x = self.register_x - (0b1111_1111 + 1)
    self.update_zero_and_negative_flags(self.register_x)

  def iny(self):
    self.register_y += 1
    # todo: Overflow -> wrapping_add
    if self.register_y > 0b1111_1111:
      self.register_y = self.register_y - (0b1111_1111 + 1)
    self.update_zero_and_negative_flags(self.register_y)

  def load_and_run(self, program: 'Vec<u8>'):
    self.load(program)
    self.reset()
    self.run()

  def load(self, program: 'Vec<u8>'):
    for n, i in enumerate(program):
      num = 0x8000 + n
      self.memory[num] = i
    self.mem_write_u16(0xFFFC, 0x8000)

  def reset(self):
    self.register_a = 0
    self.register_x = 0
    self.register_y = 0
    self.stack_pointer = STACK_RESET
    self.status = BitFlags.from_bits_truncate(0b100100)
    self.program_counter = self.mem_read_u16(0xFFFC)

  # fixme: bitflags
  def set_carry_flag(self):
    pass

  # fixme: bitflags
  def clear_carry_flag(self):
    pass

  # fixme: bitflags
  # note: ignoring decimal mode
  #   http://www.righto.com/2012/12/the-6502-overflow-flag-explained.html
  def add_to_register_a(self, data: 'u8'):
    pass

  def sbc(self, mode: '&AddressingMode'):
    addr = self.get_operand_address(mode)
    data = self.mem_read(addr)
    # fixme: neg() ?
    #self.add_to_register_a(((data as i8).wrapping_neg().wrapping_sub(1)) as u8);

  def adc(self, mode: '&AddressingMode'):
    addr = self.get_operand_address(mode)
    value = self.mem_read(addr)
    self.add_to_register_a(value)

  def stack_pop(self) -> 'u8':
    self.stack_pointer += 1
    # todo: Overflow -> wrapping_add
    if self.stack_pointer > 0b1111_1111:
      self.stack_pointer = self.stack_pointer - (0b1111_1111 + 1)
    self.mem_read(STACK + self.stack_pointer)

  def stack_push(self, data: 'u8'):
    self.mem_write((STACK + self.stack_pointer), data)
    self.stack_pointer += 1
    if self.stack_pointer > 0b1111_1111:
      self.stack_pointer = self.stack_pointer - (0b1111_1111 + 1)

  def stack_push_u16(self, data: 'u16'):
    hi = (data >> 8)
    lo = (data & 0xff)
    self.stack_push(hi)
    self.stack_push(lo)

  def stack_pop_u16(self) -> 'u16':
    lo = self.stack_pop()
    hi = self.stack_pop()
    return hi << 8 | lo

  def asl_accumulator(self):
    data = self.register_a
    if (data >> 7) == 1:
      self.set_carry_flag()
    else:
      self.clear_carry_flag()
    data = data << 1
    # fixme: return ?
    self.set_register_a(data)

  def asl(self, mode: '&AddressingMode') -> 'u8':
    addr = self.get_operand_address(mode)
    data = self.mem_read(addr)
    if (data >> 7) == 1:
      self.set_carry_flag()
    else:
      self.clear_carry_flag()
    data = data << 1
    self.mem_write(addr, data)
    self.update_zero_and_negative_flags(data)
    return data

  def lsr_accumulator(self):
    data = self.register_a
    if (data & 1) == 1:
      self.set_carry_flag()
    else:
      self.clear_carry_flag()
    data = data >> 1
    # fixme: return ?
    self.set_register_a(data)

  def lsr(self, mode: '&AddressingMode') -> 'u8':
    addr = self.get_operand_address(mode)
    data = self.mem_read(addr)
    if (data & 1) == 1:
      self.set_carry_flag()
    else:
      self.clear_carry_flag()
    data = data >> 1
    self.mem_write(addr, data)
    self.update_zero_and_negative_flags(data)
    return data

  def rol(self, mode: '&AddressingMode') -> 'u8':
    addr = self.get_operand_address(mode)
    data = self.mem_read(addr)
    # fixme: bitflags
    #old_carry = self.status.contains(CpuFlags::CARRY);
    if (data >> 7) == 1:
      self.set_carry_flag()
    else:
      self.clear_carry_flag()
    data = data << 1
    # fixme: bitflags
    #if old_carry
    self.mem_write(addr, data)
    self.update_zero_and_negative_flags(data)
    return data

  def rol_accumulator(self):
    data = self.register_a
    # fixme: bitflags
    #let old_carry = self.status.contains(CpuFlags::CARRY);
    if (data >> 7) == 1:
      self.set_carry_flag()
    else:
      self.clear_carry_flag()
    data = data << 1
    # fixme: bitflags
    #if old_carry {
    self.set_register_a(data)

  def inc(self, mode: '&AddressingMode') -> 'u8':
    addr = self.get_operand_address(mode)
    data = self.mem_read(addr)
    data = data.wrapping_add(1)
    # todo: Overflow -> wrapping_add
    if data > 0b1111_1111:
      data = data - (0b1111_1111 + 1)
    self.mem_write(addr, data)
    self.update_zero_and_negative_flags(data)
    return data

  def dey(self):
    self.register_y += 1
    if self.register_y > 0b1111_1111:
      self.register_y = self.register_y - (0b1111_1111 + 1)
    self.update_zero_and_negative_flags(self.register_y)

  def dex(self):
    self.register_x += 1
    if self.register_x > 0b1111_1111:
      self.register_x = self.register_x - (0b1111_1111 + 1)
    self.update_zero_and_negative_flags(self.register_x)

  def dec(self, mode: '&AddressingMode') -> 'u8':
    addr = self.get_operand_address(mode)
    data = self.mem_read(addr)
    data = data.wrapping_add(1)
    # todo: Overflow -> wrapping_add
    if data > 0b1111_1111:
      data = data - (0b1111_1111 + 1)
    self.mem_write(addr, data)
    self.update_zero_and_negative_flags(data)
    return data

  def pla(self):
    data = self.stack_pop()
    self.set_register_a(data)

  def plp(self):
    self.status.bits = self.stack_pop()
    # fixme: bitflags
    #self.status.remove(CpuFlags::BREAK);
    #self.status.insert(CpuFlags::BREAK2);

  def php(self):
    #http://wiki.nesdev.com/w/index.php/CPU_status_flag_behavior
    # fixme: bitflags
    #flags = self.status.clone();
    pass

  def bit(self, mode: '&AddressingMode'):
    addr = self.get_operand_address(mode)
    data = self.mem_read(addr)
    # todo: `and` -> `and_bit`
    and_bit = self.register_a & data
    # fixme: bitflags
    #if and_bit == 0:
  def compare(self, mode: '&AddressingMode', compare_with: 'u8'):
    addr = self.get_operand_address(mode)
    data = self.mem_read(addr)
    # fixme: bitflags
    #if data <= compare_with

  def branch(self, condition: 'bool'):
    # fixme: bitflags
    pass

  def run(self):
    _opcodes = opcodes.OPCODES_MAP
    # --- Loop

    # fixme: while Loop
    while True:
      code = self.mem_read(self.program_counter)
      self.program_counter += 1
      program_counter_state = self.program_counter

      opcode = _opcodes.get(code)

      # --- match
      # fixme: 未着手

      if code in (0xa9, 0xa5, 0xb5, 0xad, 0xbd, 0xb9, 0xa1, 0xb1):
        self.lda(opcode.mode)

      elif code == 0xAA:
        self.tax()

      elif code == 0xe8:
        self.inx()

      elif code == 0x00:
        print('おわり')
        break
      # --- CLD

      # --- CLI

      # --- CLV

      # --- CLC

      # --- SEC

      # --- SEI

      # --- SED

      # --- PHA

      # --- PLA

      # --- PHP

      # --- PLP

      # --- ADC

      # --- SBC

      # --- AND

      # --- EOR

      # --- ORA

      # --- LSR

      # --- LSR

      # --- ASL

      # --- ASL

      # --- ROL

      # --- ROL

      # --- ROR

      # --- ROR

      # --- INC

      # --- INY

      # --- DEC

      # --- DEX

      # --- DEY

      # --- CMP

      # --- CPY

      # --- CPX

      # --- JMP Absolute

      # --- JMP Indirect

      # --- JSR

      # --- RTS

      # --- RTI

      # --- BNE

      # --- BVS

      # --- BVC

      # --- BPL

      # --- BMI

      # --- BEQ

      # --- BCS

      # --- BCC

      # --- BIT

      # --- STA
      elif code in (0x85, 0x95, 0x8d, 0x9d, 0x99, 0x81, 0x91):
        self.sta(opcode.mode)

      # --- STX

      # --- STY

      # --- LDX

      # --- LDY

      # --- NOP

      # --- TAY

      # --- TSX

      # --- TXA

      # --- TXS

      # --- TYA

      else:
        print('todo')
        #break

      if program_counter_state == self.program_counter:
        self.program_counter += (opcode.len - 1)


if __name__ == '__main__':
  cpu = CPU()


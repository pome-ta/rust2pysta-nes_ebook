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
    # fixme: memory initialize None or 0
    #self.memory = [None] * 0xFFFF
    self.memory = [0] * 0xFFFF

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
    if result == 0:
      self.status.insert(CpuFlags.ZERO)
    else:
      self.status.remove(CpuFlags.ZERO)

    if (result & 0b1000_0000) != 0:
      self.status.insert(CpuFlags.NEGATIV)
    else:
      self.status.remove(CpuFlags.NEGATIV)

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

  def set_carry_flag(self):
    self.status.insert(CpuFlags.CARRY)

  def clear_carry_flag(self):
    self.status.remove(CpuFlags.CARRY)

  # note: ignoring decimal mode
  #   http://www.righto.com/2012/12/the-6502-overflow-flag-explained.html
  def add_to_register_a(self, data: 'u8'):
    sum = self.register_a + data
    if self.status.contains(CpuFlags.CARRY):
      sum += 1
    carry = sum > 0xff
    if carry:
      self.status.insert(CpuFlags.CARRY)
    else:
      self.status.remove(CpuFlags.CARRY)
    result = sum
    if (data ^ result) & (result ^ self.register_a) & 0x80 != 0:
      self.status.insert(CpuFlags.OVERFLOW)
    else:
      self.status.remove(CpuFlags.OVERFLOW)
    self.set_register_a(result)

  def sbc(self, mode: '&AddressingMode'):
    addr = self.get_operand_address(mode)
    data = self.mem_read(addr)
    # xxx: check print debug.
    print(f'must `u8`? -> data: {data}')
    self.add_to_register_a(0b1111_1111 - data)

  def adc(self, mode: '&AddressingMode'):
    addr = self.get_operand_address(mode)
    value = self.mem_read(addr)
    self.add_to_register_a(value)

  def stack_pop(self) -> 'u8':
    self.stack_pointer += 1
    # todo: Overflow -> wrapping_add
    if self.stack_pointer > 0b1111_1111:
      self.stack_pointer = self.stack_pointer - (0b1111_1111 + 1)
    return self.mem_read(STACK + self.stack_pointer)

  def stack_push(self, data: 'u8'):
    print('#333: ', self.stack_pointer)
    self.mem_write((STACK + self.stack_pointer), data)
    self.stack_pointer -= 1
    # xxx: check print debug.
    print(f'wrapping_sub(1) `u8`? -> stack_pointer: {self.stack_pointer}')
    # todo: Overflow -> wrapping_sub(1)
    if self.stack_pointer <= 0b0000_0000:
      self.stack_pointer = 0b1111_1111 - self.stack_pointer

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
    old_carry = self.status.contains(CpuFlags.CARRY)
    if (data >> 7) == 1:
      self.set_carry_flag()
    else:
      self.clear_carry_flag()
    data = data << 1
    if old_carry:
      data = data | 1
    self.mem_write(addr, data)
    self.update_zero_and_negative_flags(data)
    return data

  def rol_accumulator(self):
    data = self.register_a
    old_carry = self.status.contains(CpuFlags.CARRY)
    if (data >> 7) == 1:
      self.set_carry_flag()
    else:
      self.clear_carry_flag()
    data = data << 1
    if old_carry:
      data = data | 1
    self.set_register_a(data)

  def ror(self, mode: '&AddressingMode') -> 'u8':
    addr = self.get_operand_address(mode)
    data = self.mem_read(addr)
    old_carry = self.status.contains(CpuFlags.CARRY)
    if (data & 7) == 1:
      self.set_carry_flag()
    else:
      self.clear_carry_flag()
    data = data >> 1
    if old_carry:
      data = data | 0b1000_0000
    self.mem_write(addr, data)
    self.update_zero_and_negative_flags(data)
    return data

  def ror_accumulator(self):
    data = self.register_a
    old_carry = self.status.contains(CpuFlags.CARRY)
    if (data & 1) == 1:
      self.set_carry_flag()
    else:
      self.clear_carry_flag()
    data = data >> 1
    if old_carry:
      data = data | 0b1000_0000
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
    self.status.remove(CpuFlags.BREAK)
    self.status.insert(CpuFlags.BREAK2)

  def php(self):
    flags = self.status.clone()
    flags.insert(CpuFlags.BREAK)
    flags.insert(CpuFlags.BREAK2)
    self.stack_push(flags.bits)

  def bit(self, mode: '&AddressingMode'):
    addr = self.get_operand_address(mode)
    data = self.mem_read(addr)
    # todo: `and` -> `and_bit`
    and_bit = self.register_a & data
    if and_bit == 0:
      self.status.insert(CpuFlags.ZERO)
    else:
      self.status.remove(CpuFlags.ZERO)
    self.status.set(CpuFlags.NEGATIV, data & 0b1000_0000 > 0)
    self.status.set(CpuFlags.OVERFLOW, data & 0b0100_0000 > 0)

  def compare(self, mode: '&AddressingMode', compare_with: 'u8'):
    addr = self.get_operand_address(mode)
    data = self.mem_read(addr)
    if data <= compare_with:
      self.status.insert(CpuFlags.CARRY)
    else:
      self.status.remove(CpuFlags.CARRY)
    # xxx: check print debug.
    print(f'wrapping_sub(data) `u8`? -> compare_with: {compare_with}')
    # todo: Overflow -> wrapping_sub(data)
    compare_with -= data
    print(f'sub compare_with: {compare_with}')
    if compare_with <= 0b0000_0000:
      compare_with = 0b1111_1111 - compare_with
      print(f'ovr compare_with: {compare_with}')
    self.update_zero_and_negative_flags(compare_with)

  def branch(self, condition: 'bool'):
    # fixme: bitflags
    if condition:
      jump = self.mem_read(self.program_counter)
      self.program_counter += 1
      # todo: Overflow -> wrapping_add(1)
      if self.program_counter > 0b1111_1111:
        self.program_counter = self.program_counter - (0b1111_1111 + 1)
      self.program_counter += jump
      # todo: Overflow -> wrapping_add(jump)
      if self.program_counter > 0b1111_1111:
        self.program_counter = self.program_counter - (0b1111_1111 + 1)

  def run(self):
    self.run_with_callback(_, *args)

  def run_with_callback(self, *args):
    _opcodes = opcodes.OPCODES_MAP
    print('ループ')
    # --- Loop

    # fixme: while Loop
    while True:
      code = self.mem_read(self.program_counter)
      self.program_counter += 1
      program_counter_state = self.program_counter

      opcode = _opcodes.get(code)

      # --- match
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
      elif code == 0xd8:
        self.status.remove(CpuFlags.DECIMAL_MODE)

      # --- CLI
      elif code == 0x58:
        self.status.remove(CpuFlags.INTERRUPT_DISABLE)

      # --- CLV
      elif code == 0xb8:
        self.status.remove(CpuFlags.OVERFLOW)

      # --- CLC
      elif code == 0x18:
        self.clear_carry_flag()

      # --- SEC
      elif code == 0x38:
        self.set_carry_flag()

      # --- SEI
      elif code == 0x78:
        self.status.insert(CpuFlags.INTERRUPT_DISABLE)

      # --- SED
      elif code == 0xf8:
        self.status.insert(CpuFlags.DECIMAL_MODE)

      # --- PHA
      elif code == 0x48:
        self.stack_push(self.register_a)

      # --- PLA
      elif code == 0x68:
        self.pla()

      # --- PHP
      elif code == 0x08:
        self.php()

      # --- PLP
      elif code == 0x28:
        self.plp()

      # --- ADC
      elif code in (0x69, 0x65, 0x75, 0x6d, 0x7d, 0x79, 0x61):
        self.adc(opcode.mode)

      # --- SBC
      elif code in (0xe9, 0xe5, 0xf5, 0xed, 0xfd, 0xf9, 0xe1, 0xf1):
        self.sbc(opcode.mode)

      # --- AND
      elif code in (0x29, 0x25, 0x35, 0x2d, 0x3d, 0x39, 0x21, 0x31):
        self._and(opcode.mode)

      # --- EOR
      elif code in (0x49, 0x45, 0x55, 0x4d, 0x5d, 0x59, 0x41, 0x51):
        self.eor(opcode.mode)

      # --- ORA
      elif code in (0x09, 0x05, 0x15, 0x0d, 0x1d, 0x19, 0x01, 0x11):
        self.ora(opcode.mode)

      # --- LSR
      elif code == 0x4a:
        self.lsr_accumulator()

      # --- LSR
      elif code in (0x46, 0x56, 0x4e, 0x5e):
        self.lsr(opcode.mode)

      # --- ASL
      elif code == 0x0a:
        self.asl_accumulator()

      # --- ASL
      elif code in (0x06, 0x16, 0x0e, 0x1e):
        self.asl(opcode.mode)

      # --- ROL
      elif code == 0x2a:
        self.rol_accumulator()

      # --- ROL
      elif code in (0x26, 0x36, 0x2e, 0x3e):
        self.rol(opcode.mode)

      # --- ROR
      elif code == 0x6a:
        self.ror_accumulator()

      # --- ROR
      elif code in (0x66, 0x76, 0x6e, 0x7e):
        self.ror(opcode.mode)

      # --- INC
      elif code in (0xe6, 0xf6, 0xee, 0xfe):
        self.inc(opcode.mode)

      # --- INY
      elif code == 0xc8:
        self.iny()

      # --- DEC
      elif code in (0xc6, 0xd6, 0xce, 0xde):
        self.dec(opcode.mode)

      # --- DEX
      elif code == 0xca:
        self.dex()

      # --- DEY
      elif code == 0x88:
        self.dey()

      # --- CMP
      elif code in (0xc9, 0xc5, 0xd5, 0xcd, 0xdd, 0xd9, 0xc1, 0xd1):
        self.compare(opcode.mode, self.register_a)

      # --- CPY
      elif code in (0xc0, 0xc4, 0xcc):
        self.compare(opcode.mode, self.register_y)

      # --- CPX
      elif code in (0xe0, 0xe4, 0xec):
        self.compare(opcode.mode, self.register_x)

      # --- JMP Absolute
      elif code == 0x4c:
        mem_address = self.mem_read_u16(self.program_counter)
        self.program_counter = mem_address

      # --- JMP Indirect
      elif code == 0x6c:
        mem_address = self.mem_read_u16(self.program_counter)
        # let indirect_ref = self.mem_read_u16(mem_address);
        #6502 bug mode with with page boundary:
        #  if address $3000 contains $40, $30FF contains $80, and $3100 contains $50,
        # the result of JMP ($30FF) will be a transfer of control to $4080 rather than $5080 as you intended
        # i.e. the 6502 took the low byte of the address from $30FF and the high byte from $3000
        if (mem_address & 0x00FF) == 0x00FF:
          lo = self.mem_read(mem_address)
          hi = self.mem_read(mem_address & 0xFF00)
          indirect_ref = (hi) << 8 | (lo)
        else:
          indirect_ref = self.mem_read_u16(mem_address)
        self.program_counter = indirect_ref

      # --- JSR
      elif code == 0x20:
        self.stack_push_u16(self.program_counter + 2 - 1)
        target_address = self.mem_read_u16(self.program_counter)
        self.program_counter = target_address

      # --- RTS
      elif code == 0x60:
        self.program_counter = self.stack_pop_u16() + 1

      # --- RTI
      elif code == 0x40:
        self.status.bits = self.stack_pop()
        self.status.remove(CpuFlags.BREAK)
        self.status.insert(CpuFlags.BREAK2)

        self.program_counter = self.stack_pop_u16()

      # --- BNE
      elif code == 0xd0:
        self.branch(not (self.status.contains(CpuFlags.ZERO)))

      # --- BVS
      elif code == 0x70:
        self.branch(self.status.contains(CpuFlags.OVERFLOW))

      # --- BVC
      elif code == 0x50:
        self.branch(not (self.status.contains(CpuFlags.OVERFLOW)))

      # --- BPL
      elif code == 0x10:
        self.branch(not (self.status.contains(CpuFlags.NEGATIV)))

      # --- BMI
      elif code == 0x30:
        self.branch(self.status.contains(CpuFlags.NEGATIV))
      # --- BEQ
      elif code == 0xf0:
        self.branch(self.status.contains(CpuFlags.ZERO))

      # --- BCS
      elif code == 0xb0:
        self.branch(self.status.contains(CpuFlags.CARRY))
      # --- BCC
      elif code == 0x90:
        self.branch(not (self.status.contains(CpuFlags.CARRY)))

      # --- BIT
      elif code in (0x24, 0x2c):
        self.bit(opcode.mode)

      # --- STA
      elif code in (0x85, 0x95, 0x8d, 0x9d, 0x99, 0x81, 0x91):
        self.sta(opcode.mode)

      # --- STX
      elif code in (0x86, 0x96, 0x8e):
        addr = self.get_operand_address(opcode.mode)
        self.mem_write(addr, self.register_x)

      # --- STY
      elif code in (0x84, 0x94, 0x8c):
        addr = self.get_operand_address(opcode.mode)
        self.mem_write(addr, self.register_y)

      # --- LDX
      elif code in (0xa2, 0xa6, 0xb6, 0xae, 0xbe):
        self.ldx(opcode.mode)

      # --- LDY
      elif code in (0xa0, 0xa4, 0xb4, 0xac, 0xbc):
        self.ldy(opcode.mode)

      # --- NOP
      elif code == 0xea:
        # do nothing
        pass

      # --- TAY
      elif code == 0xa8:
        self.register_y = self.register_a
        self.update_zero_and_negative_flags(self.register_y)

      # --- TSX
      elif code == 0xba:
        self.register_x = self.stack_pointer
        self.update_zero_and_negative_flags(self.register_x)

      # --- TXA
      elif code == 0x8a:
        self.register_a = self.register_x
        self.update_zero_and_negative_flags(self.register_a)

      # --- TXS
      elif code == 0x9a:
        self.stack_pointer = self.register_x

      # --- TYA
      elif code == 0x98:
        self.register_a = self.register_y
        self.update_zero_and_negative_flags(self.register_a)

      else:
        print('todo')
        #break

      if program_counter_state == self.program_counter:
        self.program_counter += (opcode.len - 1)
        
      print('きた')
      print(*args)
      #self.run_with_callback(*args)


if __name__ == '__main__':
  cpu = CPU()
  cpu.register_a = 10
  cpu.load_and_run([0xe8, 0xe8, 0x00])

  pass


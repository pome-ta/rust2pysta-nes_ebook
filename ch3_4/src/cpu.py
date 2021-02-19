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
    self.bits &= ~byte

  def set(self, byte: 'u8', value: bool):
    if value:
      self.insert(byte)
    else:
      self.remove(byte)

  def clone(self):
    return copy.copy(self)




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


STACK: 'u16' = 0x0100
STACK_RESET: 'u8' = 0xfd

class CPU:
  def __init__(self):
    self.register_a: 'u8' = 0
    self.register_x: 'u8' = 0
    self.register_y: 'u8' = 0
    self.stack_pointer: 'u8' = STACK_RESET
    self.program_counter: 'u16' = 0
    self.status = BitFlags.from_bits_truncate(0b0010_0100)
    self.memory = [0] * 0xFFFF

  def mem_read(self, addr: 'u16') -> 'u8':
    return self.memory[addr]

  def mem_write(self, addr: 'u16', data: 'u8'):
    self.memory[addr] = data

  def mem_read_u16(self, pos: 'u16') -> 'u16':
    lo = self.mem_read(pos)
    hi = self.mem_read(pos + 1)
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
      addr = (pos + self.register_x) & 0xff
      return addr
    # --- 4 -> ZeroPage_Y
    elif mode == 4:
      pos = self.mem_read(self.program_counter)
      addr = (pos + self.register_y) & 0xff
      return addr
    # --- 6 -> Absolute_X
    elif mode == 6:
      base = self.mem_read_u16(self.program_counter)
      addr = (base + self.register_x) & 0xffff
      return addr
    # --- 7 -> Absolute_Y
    elif mode == 7:
      base = self.mem_read_u16(self.program_counter)
      addr = (base + self.register_y) & 0xffff
      return addr
    # --- 8 -> Indirect_X
    elif mode == 8:
      base = self.mem_read(self.program_counter)
      ptr = (base + self.register_x) & 0xff
      lo = self.mem_read(ptr)
      hi = self.mem_read((ptr + 1) & 0xffff)
      return (hi) << 8 | (lo)
    # --- 9 -> Indirect_Y
    elif mode == 9:
      base = self.mem_read(self.program_counter)
      lo = self.mem_read(base)
      hi = self.mem_read((base + 1) & 0xff)
      deref_base = (hi << 8) | (lo)
      deref = (deref_base + self.register_y) & 0xffff
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
    if (result >> 7) == 1:
      self.status.insert(CpuFlags.NEGATIV)
    else:
      self.status.remove(CpuFlags.NEGATIV)

  def update_negative_flags(self, result: 'u8'):
    if (result >> 7) == 1:
      self.status.insert(CpuFlags.NEGATIV)
    else:
      self.status.remove(CpuFlags.NEGATIV)

  def inx(self):
    self.register_x = (self.register_x + 1) & 0xff
    self.update_zero_and_negative_flags(self.register_x)

  def iny(self):
    self.register_y = (self.register_y + 1) & 0xff
    self.update_zero_and_negative_flags(self.register_y)

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
    result = sum & 0xff
    if ((data ^ result) & (result ^ self.register_a) & 0x80) != 0:
      self.status.insert(CpuFlags.OVERFLOW)
    else:
      self.status.remove(CpuFlags.OVERFLOW)
    self.set_register_a(result)

  def sbc(self, mode: '&AddressingMode'):
    addr = self.get_operand_address(mode)
    data = self.mem_read(addr)
    data = data - 0x100
    data = data * (-1) if data < 0 else data
    data = (data - 1) & 0xff
    self.add_to_register_a(data)
    
  def adc(self, mode: '&AddressingMode'):
    addr = self.get_operand_address(mode)
    value = self.mem_read(addr)
    self.add_to_register_a(value)

  def stack_pop(self) -> 'u8':
    self.stack_pointer = (self.stack_pointer + 1) & 0xff
    return self.mem_read(STACK + self.stack_pointer) 

  def stack_push(self, data: 'u8'):
    self.mem_write((STACK + self.stack_pointer), data)
    self.stack_pointer = (self.stack_pointer - 1) & 0xff

  def stack_push_u16(self, data: 'u16'):
    hi = (data >> 8)
    lo = (data & 0xff)
    self.stack_push(hi)
    self.stack_push(lo)

  def stack_pop_u16(self) -> 'u16':
    lo = self.stack_pop()
    hi = self.stack_pop()
    return (hi << 8) | lo

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
    self.update_negative_flags(data)
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
    self.update_negative_flags(data)
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
    data = (data + 1) & 0xff
    self.mem_write(addr, data)
    self.update_zero_and_negative_flags(data)
    return data

  def dey(self):
    self.register_y = (self.register_y - 1) & 0xff
    self.update_zero_and_negative_flags(self.register_y)

  def dex(self):
    self.register_x = (self.register_x - 1) & 0xff
    self.update_zero_and_negative_flags(self.register_x)

  def dec(self, mode: '&AddressingMode') -> 'u8':
    addr = self.get_operand_address(mode)
    data = self.mem_read(addr)
    data = (data - 1) & 0xff
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
    and_bit = self.register_a & data
    if and_bit == 0:
      self.status.insert(CpuFlags.ZERO)
    else:
      self.status.remove(CpuFlags.ZERO)
    self.status.set(CpuFlags.NEGATIV, (data & 0b1000_0000) > 0)
    self.status.set(CpuFlags.OVERFLOW, (data & 0b0100_0000) > 0)

  def compare(self, mode: '&AddressingMode', compare_with: 'u8'):
    addr = self.get_operand_address(mode)
    data = self.mem_read(addr)
    if data <= compare_with:
      self.status.insert(CpuFlags.CARRY)
    else:
      self.status.remove(CpuFlags.CARRY)
    compare_with = (compare_with - data) & 0xff
    self.update_zero_and_negative_flags(compare_with)

  def branch(self, condition: 'bool'):
    if condition:
      mem = self.mem_read(self.program_counter)
      jump = mem if mem < 0x80 else mem - 0x100
      self.program_counter = (self.program_counter + 1) & 0xffff
      self.program_counter = (self.program_counter + jump) & 0xffff
      
  def load_and_run(self, program: 'Vec<u8>'):
    self.load(program)
    self.reset()
    self.run()

  def load(self, program: 'Vec<u8>'):
    for n, i in enumerate(program):
      num = 0x0600 + n
      self.memory[num] = i
    self.mem_write_u16(0xFFFC, 0x0600)

  def reset(self):
    self.register_a = 0
    self.register_x = 0
    self.register_y = 0
    self.stack_pointer = STACK_RESET
    self.status = BitFlags.from_bits_truncate(0b0010_0100)
    self.program_counter = self.mem_read_u16(0xFFFC)

  def run(self):
    pass

  def run_with_callback(self):
    _opcodes = opcodes.OPCODES_MAP
    code = self.mem_read(self.program_counter)
    self.program_counter += 1
    program_counter_state = self.program_counter
    opcode = _opcodes.get(code)
    # --- match
    if code in (0xa9, 0xa5, 0xb5, 0xad, 0xbd, 0xb9, 0xa1, 0xb1):  # 169, 165, 181, 173, 189, 185, 161, 177
      self.lda(opcode.mode)
    
    elif code == 0xAA:  # 170
      self.tax()
    
    elif code == 0xe8:  # 232
      self.inx()
    
    elif code == 0x00:  # 0
      return 
    
    # --- CLD
    elif code == 0xd8:  # 216
      self.status.remove(CpuFlags.DECIMAL_MODE)
    
    # --- CLI
    elif code == 0x58:  # 88
      self.status.remove(CpuFlags.INTERRUPT_DISABLE)
    
    # --- CLV
    elif code == 0xb8:  # 184
      self.status.remove(CpuFlags.OVERFLOW)

    # --- CLC
    elif code == 0x18:  # 24
      self.clear_carry_flag()

    # --- SEC
    elif code == 0x38:  # 56
      self.set_carry_flag()

    # --- SEI
    elif code == 0x78:  # 120
      self.status.insert(CpuFlags.INTERRUPT_DISABLE)

    # --- SED
    elif code == 0xf8:  # 248
      self.status.insert(CpuFlags.DECIMAL_MODE)

    # --- PHA
    elif code == 0x48:  # 72
      self.stack_push(self.register_a)

    # --- PLA
    elif code == 0x68:  # 104
      self.pla()

    # --- PHP
    elif code == 0x08:  # 8
      self.php()

    # --- PLP
    elif code == 0x28:  # 40
      self.plp()

    # --- ADC
    elif code in (0x69, 0x65, 0x75, 0x6d, 0x7d, 0x79, 0x61):  # 105, 101, 117, 109, 125, 121, 97
      self.adc(opcode.mode)

    # --- SBC
    elif code in (0xe9, 0xe5, 0xf5, 0xed, 0xfd, 0xf9, 0xe1, 0xf1):  # 233, 229, 245, 237, 253, 249, 225, 241
      self.sbc(opcode.mode)

    # --- AND
    elif code in (0x29, 0x25, 0x35, 0x2d, 0x3d, 0x39, 0x21, 0x31):  # 41, 37, 53, 45, 61, 57, 33, 49
      self._and(opcode.mode)

    # --- EOR
    elif code in (0x49, 0x45, 0x55, 0x4d, 0x5d, 0x59, 0x41, 0x51):  # 73, 69, 85, 77, 93, 89, 65, 81
      self.eor(opcode.mode)

    # --- ORA
    elif code in (0x09, 0x05, 0x15, 0x0d, 0x1d, 0x19, 0x01, 0x11):  # 9, 5, 21, 13, 29, 25, 1, 17
      self.ora(opcode.mode)

    # --- LSR
    elif code == 0x4a:  # 74
      self.lsr_accumulator()

    # --- LSR
    elif code in (0x46, 0x56, 0x4e, 0x5e):  # 70, 86, 78, 94
      self.lsr(opcode.mode)

    # --- ASL
    elif code == 0x0a:  # 10
      self.asl_accumulator()

    # --- ASL
    elif code in (0x06, 0x16, 0x0e, 0x1e):  # 6, 22, 14, 30
      self.asl(opcode.mode)

    # --- ROL
    elif code == 0x2a:  # 42
      self.rol_accumulator()

    # --- ROL
    elif code in (0x26, 0x36, 0x2e, 0x3e):  # 38, 54, 46, 62
      self.rol(opcode.mode)

    # --- ROR
    elif code == 0x6a:  # 106
      self.ror_accumulator()

    # --- ROR
    elif code in (0x66, 0x76, 0x6e, 0x7e):  # 102, 118, 110, 126
      self.ror(opcode.mode)

    # --- INC
    elif code in (0xe6, 0xf6, 0xee, 0xfe):  # 230, 246, 238, 254
      self.inc(opcode.mode)

    # --- INY
    elif code == 0xc8:  # 200
      self.iny()

    # --- DEC
    elif code in (0xc6, 0xd6, 0xce, 0xde):  # 198, 214, 206, 222
      self.dec(opcode.mode)

    # --- DEX
    elif code == 0xca:  # 202
      self.dex()

    # --- DEY
    elif code == 0x88:  # 136
      self.dey()

    # --- CMP
    elif code in (0xc9, 0xc5, 0xd5, 0xcd, 0xdd, 0xd9, 0xc1, 0xd1):  # 201, 197, 213, 205, 221, 217, 193, 209
      self.compare(opcode.mode, self.register_a)

    # --- CPY
    elif code in (0xc0, 0xc4, 0xcc):  # 192, 196, 204
      self.compare(opcode.mode, self.register_y)

    # --- CPX
    elif code in (0xe0, 0xe4, 0xec):  # 224, 228, 236
      self.compare(opcode.mode, self.register_x)

    # --- JMP Absolute
    elif code == 0x4c:  # 76
      mem_address = self.mem_read_u16(self.program_counter)
      self.program_counter = mem_address

    # --- JMP Indirect
    elif code == 0x6c:  # 108
      mem_address = self.mem_read_u16(self.program_counter)
      # let indirect_ref = self.mem_read_u16(mem_address);
      #6502 bug mode with with page boundary:
      #  if address $3000 contains $40, $30FF contains $80, and $3100 contains $50,
      # the result of JMP ($30FF) will be a transfer of control to $4080 rather than $5080 as you intended
      # i.e. the 6502 took the low byte of the address from $30FF and the high byte from $3000
      if (mem_address & 0x00FF) == 0x00FF:
        lo = self.mem_read(mem_address)
        hi = self.mem_read(mem_address & 0xFF00)
        indirect_ref = (hi << 8) | (lo)
      else:
        indirect_ref = self.mem_read_u16(mem_address)
      self.program_counter = indirect_ref

    # --- JSR
    elif code == 0x20:  # 32
      self.stack_push_u16(self.program_counter + 2 - 1)
      target_address = self.mem_read_u16(self.program_counter)
      self.program_counter = target_address

    # --- RTS
    elif code == 0x60:  # 96
      self.program_counter = self.stack_pop_u16() + 1

    # --- RTI
    elif code == 0x40:  # 64
      self.status.bits = self.stack_pop()
      self.status.remove(CpuFlags.BREAK)
      self.status.insert(CpuFlags.BREAK2)
      self.program_counter = self.stack_pop_u16()

    # --- BNE
    elif code == 0xd0:  # 208
      self.branch(not self.status.contains(CpuFlags.ZERO))

    # --- BVS
    elif code == 0x70:  # 112
      self.branch(self.status.contains(CpuFlags.OVERFLOW))

    # --- BVC
    elif code == 0x50:  # 80
      self.branch(not (self.status.contains(CpuFlags.OVERFLOW)))

    # --- BPL
    elif code == 0x10:  # 16
      self.branch(not (self.status.contains(CpuFlags.NEGATIV)))

    # --- BMI
    elif code == 0x30:  # 48
      self.branch(self.status.contains(CpuFlags.NEGATIV))
    
    # --- BEQ
    elif code == 0xf0:  # 240
      self.branch(self.status.contains(CpuFlags.ZERO))

    # --- BCS
    elif code == 0xb0:  # 176
      self.branch(self.status.contains(CpuFlags.CARRY))
    # --- BCC
    elif code == 0x90:  # 144
      self.branch(not (self.status.contains(CpuFlags.CARRY)))

    # --- BIT
    elif code in (0x24, 0x2c):  # 36, 44
      self.bit(opcode.mode)

    # --- STA
    elif code in (0x85, 0x95, 0x8d, 0x9d, 0x99, 0x81, 0x91):  # 133, 149, 141, 157, 153, 129, 145
      self.sta(opcode.mode)

    # --- STX
    elif code in (0x86, 0x96, 0x8e):  # 134, 150, 142
      addr = self.get_operand_address(opcode.mode)
      self.mem_write(addr, self.register_x)

    # --- STY
    elif code in (0x84, 0x94, 0x8c):  # 132, 148, 140
      addr = self.get_operand_address(opcode.mode)
      self.mem_write(addr, self.register_y)

    # --- LDX
    elif code in (0xa2, 0xa6, 0xb6, 0xae, 0xbe):  # 162, 166, 182, 174, 190
      self.ldx(opcode.mode)

    # --- LDY
    elif code in (0xa0, 0xa4, 0xb4, 0xac, 0xbc):  # 160, 164, 180, 172, 188
      self.ldy(opcode.mode)

    # --- NOP
    elif code == 0xea:  #234
      # do nothing
      pass

    # --- TAY
    elif code == 0xa8:  # 168
      self.register_y = self.register_a
      self.update_zero_and_negative_flags(self.register_y)

    # --- TSX
    elif code == 0xba:  # 186
      self.register_x = self.stack_pointer
      self.update_zero_and_negative_flags(self.register_x)

    # --- TXA
    elif code == 0x8a:  # 138
      self.register_a = self.register_x
      self.update_zero_and_negative_flags(self.register_a)

    # --- TXS
    elif code == 0x9a:  # 154
      self.stack_pointer = self.register_x

    # --- TYA
    elif code == 0x98:  # 152
      self.register_a = self.register_y
      self.update_zero_and_negative_flags(self.register_a)

    else:
      print('todo')
      #break

    if program_counter_state == self.program_counter:
      self.program_counter += (opcode.len - 1)
    
    return


if __name__ == '__main__':
  game_code = [
    0xa2, 0x00, 0xa0, 0x00, 0x8a, 0x99, 0x00, 0x02, 0x48, 0xe8, 0xc8, 0xc0, 0x10, 0xd0, 0xf5, 0x68, 0x99, 0x00, 0x02, 0xc8, 0xc0, 0x20, 0xd0, 0xf7
  ]  
  
  cpu = CPU()
  cpu.load(game_code)
  cpu.reset()
  

from enum import Flag, auto


class AddressingMode(Flag):
  Immediate = auto()
  ZeroPage = auto()
  ZeroPage_X = auto()
  ZeroPage_Y = auto()
  Absolute = auto()
  Absolute_X = auto()
  Absolute_Y = auto()
  Indirect_X = auto()
  Indirect_Y = auto()
  NoneAddressing = auto()


import opcodes


class CPU:
  def __init__(self):
    self.register_a: 'u8' = 0
    self.register_x: 'u8' = 0
    self.register_y: 'u8' = 0
    self.status: 'u8' = 0
    self.program_counter: 'u16' = 0
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
    if mode == AddressingMode.Immediate:
      return self.program_counter

    elif mode == AddressingMode.ZeroPage:
      return self.mem_read(self.program_counter)

    elif mode == AddressingMode.Absolute:
      return self.mem_read_u16(self.program_counter)

    elif mode == AddressingMode.ZeroPage_X:
      pos = self.mem_read(self.program_counter)
      addr = pos + self.register_x
      # todo: Overflow -> wrapping_add
      if addr > 0b1111_1111:
        addr = addr - (0b1111_1111 + 1)
      return addr

    elif mode == AddressingMode.ZeroPage_Y:
      pos = self.mem_read(self.program_counter)
      addr = pos + self.register_y
      # todo: Overflow -> wrapping_add
      if addr > 0b1111_1111:
        addr = addr - (0b1111_1111 + 1)
      return addr

    elif mode == AddressingMode.Absolute_X:
      base = self.mem_read_u16(self.program_counter)
      addr = base + self.register_x
      # todo: Overflow -> wrapping_add
      if addr > 0b1111_1111:
        addr = addr - (0b1111_1111 + 1)
      return addr

    elif mode == AddressingMode.Absolute_Y:
      base = self.mem_read_u16(self.program_counter)
      addr = base + self.register_y
      # todo: Overflow -> wrapping_add
      if addr > 0b1111_1111:
        addr = addr - (0b1111_1111 + 1)
      return addr

    elif mode == AddressingMode.Indirect_X:
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

    elif mode == AddressingMode.Indirect_Y:
      base = self.mem_read(self.program_counter)
      lo = self.mem_read(base)
      base += 1
      # todo: Overflow -> wrapping_add
      if base > 0b1111_1111:
        base = base - (0b1111_1111 + 1)
      hi = self.mem_read(base)
      deref_base = (hi) << 8 | (lo)
      deref = deref + self.register_y
      # todo: Overflow -> wrapping_add
      if deref > 0b1111_1111:
        deref = deref - (0b1111_1111 + 1)
      return deref

    elif mode == AddressingMode.NoneAddressing:
      print(f'mode {mode} is not supported')

  def lda(self, mode: '&AddressingMode'):
    addr = self.get_operand_address(mode)
    value = self.mem_read(addr)
    self.register_a = value
    self.update_zero_and_negative_flags(self.register_a)

  def sta(self, mode: '&AddressingMode'):
    addr = self.get_operand_address(mode)
    self.mem_write(addr, self.register_a)

  def tax(self):
    self.register_x = self.register_a
    self.update_zero_and_negative_flags(self.register_x)

  def update_zero_and_negative_flags(self, result: 'u8'):
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
    self.status = 0
    self.program_counter = self.mem_read_u16(0xFFFC)

  def run(self):
    _opcodes = opcodes.OPCODES_MAP
    # --- Loop
    # note: we move  intialization of program_counter from here to load function
    # note: プログラムカウンタの初期化をここからロード関数に移動します
    # fixme: while Loop
    while True:
      code = self.mem_read(self.program_counter)
      self.program_counter += 1
      program_counter_state = self.program_counter

      opcode = _opcodes.get(code)
      print(opcode.mode == AddressingMode.Immediate)
      print(type(opcode.mode))
      print(type(AddressingMode.Immediate))
      print(opcode.mode)
      

      # --- match
      if code in (0xa9, 0xa5, 0xb5, 0xad, 0xbd, 0xb9, 0xa1, 0xb1):
        self.lda(opcode.mode)

      elif code in (0x85, 0x95, 0x8d, 0x9d, 0x99, 0x81, 0x91):
        self.sta(opcode.mode)

      elif code == 0xAA:
        self.tax()

      elif code == 0xe8:
        self.inx()

      elif code == 0x00:
        print('おわり')
        break

      else:
        print('todo')
        #break

      if program_counter_state == self.program_counter:
        self.program_counter += (opcode.len - 1)


if __name__ == '__main__':
  cpu = CPU()
  cpu.load_and_run([0xa9, 0xc0, 0xaa, 0xe8, 0x00])


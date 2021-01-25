from cpu import AddressingMode

# todo: [namedtuple](https://qiita.com/Seny/items/add4d03876f505442136)


class OpCode:
  def __init__(self,
               code: 'u8',
               mnemonic: "&'static str",
               len: 'u8',
               cycles: 'u8',
               mode: 'AddressingMode'):
    self.code = code
    self.mnemonic = mnemonic
    self.len = len
    self.cycles = cycles
    self.mode = mode


CPU_OPS_CODES = [
  OpCode(0x00, 'BRK', 1, 7, AddressingMode.NoneAddressing),
  OpCode(0xaa, 'TAX', 1, 2, AddressingMode.NoneAddressing),
  OpCode(0xe8, 'INX', 1, 2, AddressingMode.NoneAddressing),
  
  OpCode(0xa9, 'LDA', 2, 2, AddressingMode.Immediate),
  OpCode(0xa5, 'LDA', 2, 3, AddressingMode.ZeroPage),
  OpCode(0xb5, 'LDA', 2, 4, AddressingMode.ZeroPage_X),
  OpCode(0xad, 'LDA', 3, 4, AddressingMode.Absolute),
  # /*+1 if page crossed*/
  OpCode(0xbd, 'LDA', 3, 4, AddressingMode.Absolute_X),
  # /*+1 if page crossed*/
  OpCode(0xb9, 'LDA', 3, 4, AddressingMode.Absolute_Y),
  OpCode(0xa1, 'LDA', 2, 6, AddressingMode.Indirect_X),
  # /*+1 if page crossed*/
  OpCode(0xb1, 'LDA', 2, 5, AddressingMode.Indirect_Y),
  
  OpCode(0x85, 'STA', 2, 3, AddressingMode.ZeroPage),
  OpCode(0x95, 'STA', 2, 4, AddressingMode.ZeroPage_X),
  OpCode(0x8d, 'STA', 3, 4, AddressingMode.Absolute),
  OpCode(0x9d, 'STA', 3, 5, AddressingMode.Absolute_X),
  OpCode(0x99, 'STA', 3, 5, AddressingMode.Absolute_Y),
  OpCode(0x81, 'STA', 2, 6, AddressingMode.Indirect_X),
  OpCode(0x91, 'STA', 2, 6, AddressingMode.Indirect_Y),
]

OPCODES_MAP = {}
for cpuop in CPU_OPS_CODES:
  OPCODES_MAP.update({cpuop.code: cpuop})

if __name__ == '__main__':
  pass


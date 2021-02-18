from cartridge import Rom
from cpu import Mem

#  _______________ $10000  _______________
# | PRG-ROM       |       |               |
# | Upper Bank    |       |               |
# |_ _ _ _ _ _ _ _| $C000 | PRG-ROM       |
# | PRG-ROM       |       |               |
# | Lower Bank    |       |               |
# |_______________| $8000 |_______________|
# | SRAM          |       | SRAM          |
# |_______________| $6000 |_______________|
# | Expansion ROM |       | Expansion ROM |
# |_______________| $4020 |_______________|
# | I/O Registers |       |               |
# |_ _ _ _ _ _ _ _| $4000 |               |
# | Mirrors       |       | I/O Registers |
# | $2000-$2007   |       |               |
# |_ _ _ _ _ _ _ _| $2008 |               |
# | I/O Registers |       |               |
# |_______________| $2000 |_______________|
# | Mirrors       |       |               |
# | $0000-$07FF   |       |               |
# |_ _ _ _ _ _ _ _| $0800 |               |
# | RAM           |       | RAM           |
# |_ _ _ _ _ _ _ _| $0200 |               |
# | Stack         |       |               |
# |_ _ _ _ _ _ _ _| $0100 |               |
# | Zero Page     |       |               |
# |_______________| $0000 |_______________|

RAM: 'u16' = 0x0000
RAM_MIRRORS_END: 'u16' = 0x1FFF
PPU_REGISTERS: 'u16' = 0x2000
PPU_REGISTERS_MIRRORS_END: 'u16' = 0x3FFF


class Bus(Mem):
  def __init__(self, rom: 'Rom'):
    self.cpu_vram: '[u8; 2048]' = [0] * 2048
    self.rom = rom

  def read_prg_rom(self, addr: 'u16') -> 'u8':
    addr -= 0x8000
    if len(self.rom.prg_rom) == 0x4000 and addr >= 0x4000:
      # mirror if needed
      addr = addr % 0x4000
    return self.rom.prg_rom[addr]

  def mem_read(self, addr: 'u16') -> 'u8':
    if addr in range(RAM, RAM_MIRRORS_END):
      mirror_down_addr = addr & 0b0000_0111_1111_1111
      return self.cpu_vram[mirror_down_addr]
    elif addr in range(PPU_REGISTERS, PPU_REGISTERS_MIRRORS_END):
      _mirror_down_addr = addr & 0b0010_0000_0000_0111
      print('PPU is not supported yet')
    elif addr in range(0x8000, 0xFFFF):
      return self.read_prg_rom(addr)
    else:
      print(f'Ignoring mem access at addr:{addr}')
      return 0

  def mem_write(self, addr: 'u16', data: 'u8'):
    if addr in range(RAM, RAM_MIRRORS_END):
      mirror_down_addr = addr & 0b0000_0111_1111_1111
      self.cpu_vram[mirror_down_addr] = data
    elif addr in range(PPU_REGISTERS, PPU_REGISTERS_MIRRORS_END):
      _mirror_down_addr = addr & 0b0010_0000_0000_0111
      print('PPU is not supported yet')
    elif addr in range(0x8000, 0xFFFF):
      print('Attempt to write to Cartridge ROM space')
    else:
      print(f'Ignoring mem write-access at addr:{addr}')


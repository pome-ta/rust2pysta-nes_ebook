from typing import NamedTuple

#NES_TAG: '[u8; 4]' = [0x4E, 0x45, 0x53, 0x1A]
NES_TAG = b'NES\x1a'
PRG_ROM_PAGE_SIZE: 'usize' = 16384
CHR_ROM_PAGE_SIZE: 'usize' = 8192


class _Mirroring(NamedTuple):
  VERTICAL: int = 1
  HORIZONTAL: int = 2
  FOUR_SCREEN: int = 3


Mirroring = _Mirroring()


class Rom:
  def __init__(self, raw: '&Vec<u8>'):
    if raw[0:4] != NES_TAG:
      print('File is not in iNES file format')
    mapper: 'u8' = (raw[7] & 0b1111_0000) | (raw[6] >> 4)
    ines_ver = (raw[7] >> 2) & 0b11
    if ines_ver != 0:
      print('NES2.0 format is not supported')
    four_screen = raw[6] & 0b1000 != 0
    vertical_mirroring = raw[6] & 0b1 != 0

    if four_screen == True:
      screen_mirroring: 'Mirroring' = Mirroring.FOUR_SCREEN
    elif vertical_mirroring == True and four_screen == False:
      screen_mirroring: 'Mirroring' = Mirroring.VERTICAL
    elif four_screen == False and vertical_mirroring == False:
      screen_mirroring: 'Mirroring' = Mirroring.HORIZONTAL

    prg_rom_size = raw[4] * PRG_ROM_PAGE_SIZE
    chr_rom_size = raw[5] * CHR_ROM_PAGE_SIZE
    skip_trainer = raw[6] & 0b100 != 0
    prg_rom_start = 16 + (512 if skip_trainer else 0)
    chr_rom_start = prg_rom_start + prg_rom_size

    self.prg_rom: 'Vec<u8>' = raw[prg_rom_start:(prg_rom_start + prg_rom_size)]
    self.chr_rom: 'Vec<u8>' = raw[chr_rom_start:(chr_rom_start + chr_rom_size)]
    self.mapper: 'u8' = mapper
    self.screen_mirroring: 'Mirroring' = screen_mirroring
    self.ok()

  def ok(self) -> 'Result<Rom, String>':
    return (self.prg_rom, self.chr_rom, self.mapper, self.screen_mirroring)


if __name__ == '__main__':
  import pathlib

  PATH = '../'
  ROM = 'hello'
  NES_PATH = pathlib.Path(PATH + ROM + '.nes')
  # xxx: list or tuple ?
  nes_bytes = pathlib.Path.read_bytes(NES_PATH)

  rom = Rom(nes_bytes)


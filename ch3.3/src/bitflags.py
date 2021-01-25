from enum import Flag

class CpuFlags(Flag):
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


if __name__ == '__main__':
  cpu_flags = CpuFlags
  

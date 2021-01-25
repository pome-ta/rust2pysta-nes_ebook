from enum import IntFlag


class Flags(IntFlag):
  """
  
  """
  A = 0b0000_0001
  B = 0b0000_0010
  C = 0b0000_0100
  ABC = A | B | C
  
  
  

if __name__ == '__main__':
  pass
  
  


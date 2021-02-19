class CPU:
  def __init__(self):
    self.register_a: 'u8' = 0
    self.register_x: 'u8' = 0
    self.status: 'u8' = 0
    self.program_counter: 'u16' = 0

  def lda(self, value: 'u8') :
    self.register_a = value
    self.update_zero_and_negative_flags(self.register_a)

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
      print('in', self.register_x)
      self.register_x = self.register_x - (0b1111_1111 + 1)
      print('ot', self.register_x)
    
    
    self.update_zero_and_negative_flags(self.register_x)

  def interpret(self, program: 'Vec<u8>'):
    self.program_counter = 0
    while True:
      # --- loop
      opscode = program[self.program_counter]
      self.program_counter += 1
      # --- match
      if opscode == 0xA9:
        param = program[self.program_counter]
        self.program_counter += 1
        self.lda(param)
      elif opscode == 0xAA:
        self.tax()
      elif opscode == 0xe8:
        self.inx()
      elif opscode == 0x00:
        print('0x00')
        break
      else:
        print('todo')
        break


if __name__ == '__main__':
  cpu = CPU()
  #cpu.interpret([0xa9, 0xc0, 0xaa, 0xe8, 0x00])
  cpu.register_x = 0xff
  cpu.interpret([0xe8, 0xe8, 0x00])
  print(':',cpu.register_x)


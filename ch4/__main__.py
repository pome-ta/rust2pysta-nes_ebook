from itertools import product
from random import randint
from io import BytesIO

import ui
import numpy as np
from PIL import Image as ImageP

from cpu import CPU
from bus import Bus


game_code = [
  0x20, 0x06, 0x06, 0x20, 0x38, 0x06, 0x20, 0x0d, 0x06, 0x20, 0x2a, 0x06, 0x60, 0xa9, 0x02,
  0x85, 0x02, 0xa9, 0x04, 0x85, 0x03, 0xa9, 0x11, 0x85, 0x10, 0xa9, 0x10, 0x85, 0x12, 0xa9,
  0x0f, 0x85, 0x14, 0xa9, 0x04, 0x85, 0x11, 0x85, 0x13, 0x85, 0x15, 0x60, 0xa5, 0xfe, 0x85,
  0x00, 0xa5, 0xfe, 0x29, 0x03, 0x18, 0x69, 0x02, 0x85, 0x01, 0x60, 0x20, 0x4d, 0x06, 0x20,
  0x8d, 0x06, 0x20, 0xc3, 0x06, 0x20, 0x19, 0x07, 0x20, 0x20, 0x07, 0x20, 0x2d, 0x07, 0x4c,
  0x38, 0x06, 0xa5, 0xff, 0xc9, 0x77, 0xf0, 0x0d, 0xc9, 0x64, 0xf0, 0x14, 0xc9, 0x73, 0xf0,
  0x1b, 0xc9, 0x61, 0xf0, 0x22, 0x60, 0xa9, 0x04, 0x24, 0x02, 0xd0, 0x26, 0xa9, 0x01, 0x85,
  0x02, 0x60, 0xa9, 0x08, 0x24, 0x02, 0xd0, 0x1b, 0xa9, 0x02, 0x85, 0x02, 0x60, 0xa9, 0x01,
  0x24, 0x02, 0xd0, 0x10, 0xa9, 0x04, 0x85, 0x02, 0x60, 0xa9, 0x02, 0x24, 0x02, 0xd0, 0x05,
  0xa9, 0x08, 0x85, 0x02, 0x60, 0x60, 0x20, 0x94, 0x06, 0x20, 0xa8, 0x06, 0x60, 0xa5, 0x00,
  0xc5, 0x10, 0xd0, 0x0d, 0xa5, 0x01, 0xc5, 0x11, 0xd0, 0x07, 0xe6, 0x03, 0xe6, 0x03, 0x20,
  0x2a, 0x06, 0x60, 0xa2, 0x02, 0xb5, 0x10, 0xc5, 0x10, 0xd0, 0x06, 0xb5, 0x11, 0xc5, 0x11,
  0xf0, 0x09, 0xe8, 0xe8, 0xe4, 0x03, 0xf0, 0x06, 0x4c, 0xaa, 0x06, 0x4c, 0x35, 0x07, 0x60,
  0xa6, 0x03, 0xca, 0x8a, 0xb5, 0x10, 0x95, 0x12, 0xca, 0x10, 0xf9, 0xa5, 0x02, 0x4a, 0xb0,
  0x09, 0x4a, 0xb0, 0x19, 0x4a, 0xb0, 0x1f, 0x4a, 0xb0, 0x2f, 0xa5, 0x10, 0x38, 0xe9, 0x20,
  0x85, 0x10, 0x90, 0x01, 0x60, 0xc6, 0x11, 0xa9, 0x01, 0xc5, 0x11, 0xf0, 0x28, 0x60, 0xe6,
  0x10, 0xa9, 0x1f, 0x24, 0x10, 0xf0, 0x1f, 0x60, 0xa5, 0x10, 0x18, 0x69, 0x20, 0x85, 0x10,
  0xb0, 0x01, 0x60, 0xe6, 0x11, 0xa9, 0x06, 0xc5, 0x11, 0xf0, 0x0c, 0x60, 0xc6, 0x10, 0xa5,
  0x10, 0x29, 0x1f, 0xc9, 0x1f, 0xf0, 0x01, 0x60, 0x4c, 0x35, 0x07, 0xa0, 0x00, 0xa5, 0xfe,
  0x91, 0x00, 0x60, 0xa6, 0x03, 0xa9, 0x00, 0x81, 0x10, 0xa2, 0x00, 0xa9, 0x01, 0x81, 0x10,
  0x60, 0xa6, 0xff, 0xea, 0xea, 0xca, 0xd0, 0xfb, 0x60,
]

init_img = ImageP.new('RGB', (32, 32))
base_array = np.asarray(init_img)
diff_array = np.zeros((32, 32, 3), dtype=np.uint8)

BLACK = '#000000'
WHITE = '#ffffff'
GREY = '#808080'
RED = '#ff0000'
GREEN = '#008000'
BLUE = '#0000ff'
MAGENTA = '#ff00ff'
YELLOW = '#ffff00'
CYAN = '#00ffff'


def palette(c_byt: 'u8'):
  if c_byt == 0:  # 0 => BLACK
    return BLACK
  elif c_byt == 1:  # 1 => WHITE
    return WHITE
  elif c_byt in (2, 9):  # 2 | 9 => GREY
    return GREY
  elif c_byt in (3, 10):  # 3 | 10 => RED
    return RED
  elif c_byt in (4, 11):  # 4 | 11 => GREEN
    return GREEN
  elif c_byt in (5, 12):  # 5 | 12 => BLUE
    return BLUE
  elif c_byt in (6, 13):  # 6 | 13 => MAGENTA
    return MAGENTA
  elif c_byt in (7, 14):  # 7 | 14 => YELLOW
    return YELLOW
  else:  # _ => CYAN
    return CYAN


def color(byt: str) -> list:
  head = '0x'
  r = int(head + byt[1:3], 16)
  g = int(head + byt[3:5], 16)
  b = int(head + byt[5:7], 16)
  num_rgb = np.array([r, g, b], dtype=np.uint8)
  return num_rgb


def show_canvas(_cpu):
  #canvas = _cpu.memory[0x200:0x600]
  #canvas = [_cpu.mem_read(i) for i in range(0x200, 0x600)]
  canvas = _cpu.bus.cpu_vram[0x200:0x600]
  count = 0
  for x, y in product(range(32), range(32)):
    byt = canvas[count]
    diff_array[x][y] = color(palette(byt))
    count += 1
  del canvas
  out_array = base_array + diff_array
  out_img = ImageP.fromarray(out_array)
  re_out = out_img.resize((320, 320))
  with BytesIO() as bIO:
    re_out.save(bIO, 'png')
    re_img = ui.Image.from_data(bIO.getvalue())
    del bIO
    return re_img


class Key(ui.View):
  def __init__(self, call: 'CPU.mem_write', byte_key: int):
    self.call = call
    self.byte_key = byte_key
    self.bg_color = GREY
    self.height = 64
    self.width = 64
    self.alpha = 1

  def touch_began(self, touch):
    self.alpha = .25
    self.call(0xff, self.byte_key)

  def touch_ended(self, touch):
    self.alpha = 1


class View(ui.View):
  def __init__(self):
    self.name = 'View'
    self.bg_color = .128
    self.update_interval = 1 / (2 ** 14)
    bus = Bus()
    self.cpu = CPU(bus)
    self.cpu.load(game_code)
    self.cpu.reset()
    self.cpu.program_counter = 0x0600
    self.screen_state = np.array([0] * (32 * 32), dtype=np.uint8)
    #self.cpu.mem_write(0xfe, randint(1, 16))
    #self.cpu.run_with_callback()

    self.im_view = ui.ImageView()
    self.im_view.bg_color = 0
    self.im_view.height = 320
    self.im_view.width = 320
    self.im_view.image = show_canvas(self.cpu)
    self.add_subview(self.im_view)

    self.key_W = Key(self.cpu.mem_write, 0x77)
    self.key_S = Key(self.cpu.mem_write, 0x73)
    self.key_A = Key(self.cpu.mem_write, 0x61)
    self.key_D = Key(self.cpu.mem_write, 0x64)
    self.add_subview(self.key_W)
    self.add_subview(self.key_S)
    self.add_subview(self.key_A)
    self.add_subview(self.key_D)

  def read_screen_state(self, _cpu: '&CPU') -> bool:
    update = False
    pre_array = self.screen_state
    #memory = [_cpu.mem_read(i) for i in range(0x200, 0x600)]
    memory = _cpu.bus.cpu_vram[0x200:0x600]
    mem_array = np.array(memory, dtype=np.uint8)
    #del memory
    buf_array = pre_array - mem_array
    if np.all(buf_array == 0):
      update = False
    else:
      self.screen_state = mem_array
      update = True
    return update

  def update(self):
    self.cpu.mem_write(0xfe, randint(1, 16))
    if self.read_screen_state(self.cpu):
      self.im_view.image = show_canvas(self.cpu)
    
    self.cpu.run_with_callback()

  def layout(self):
    self.im_view.x = (self.width * .5) - (self.im_view.width * .5)
    self.key_W.x = self.key_S.x = self.key_A.x = self.key_D.x = (
      self.width * .5) - (self.key_W.width * .5)
    self.key_W.y = self.key_S.y = self.key_A.y = self.key_D.y = self.height * .64
    self.key_W.y -= self.key_W.height
    self.key_S.y += self.key_S.height
    self.key_A.x -= self.key_A.width
    self.key_D.x += self.key_D.width


if __name__ == '__main__':
  view = View()
  view.present('fullscreen')


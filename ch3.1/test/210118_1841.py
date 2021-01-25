from ctypes import Structure, c_ubyte

class CCC(Structure):
  _fields_ = (
    ('x', c_ubyte),
    ('y', c_ubyte))


num = 0b1111_1111

ccc = CCC()
ccc.x = 5

print(num)

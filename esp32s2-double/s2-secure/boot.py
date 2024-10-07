from os import listdir
from machine import reset

#my basic API
def readfile(filename):
    with open(filename) as f:
        return f.read()
def gccollect():
    from gc import collect
    gc.collect()

class __ANY:
    @property
    def ls(self):
        return listdir()
__any = __ANY()
ls = __any.ls

import wificonnect

expected_lib = ['base64.mpy', 'binascii.mpy', 'hmac.mpy', 'struct.mpy']

try:
    assert(listdir('/lib')==expected_lib)
except:
    import libinstall

#main app
import securelemakin

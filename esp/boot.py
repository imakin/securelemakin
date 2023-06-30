import os

import wificonnect
import time

expected_lib = ['base64.mpy', 'binascii.mpy', 'hmac.mpy', 'struct.mpy']

try:
    assert(os.listdir('/lib')==expected_lib)
except:
    import libinstall

#my basic API
def readfile(filename):
    with open(filename) as f:
        return f.read()

#main app
import atmega32u4

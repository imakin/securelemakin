#!/usr/bin/env python
import os
import subprocess
import sys

def upload(filename):
  cmd = f"pyboard.py -d /dev/tty.usbmodem* -f cp {filename} :{filename}"
  o = subprocess.check_output(cmd,shell=True)
  print(o.decode('utf8'))

try:
  upload(sys.argv[1])
except:
  print(f"{__FILE__} [filenname to upload]")

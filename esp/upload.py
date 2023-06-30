#!/usr/bin/env python
#requirement: pyserial, python-minifier

import os
import subprocess
import sys

import python_minifier


device = "/dev/tty.usb*" #mac
try:
  o = subprocess.check_output(f"ls {device}",shell=True)
except:
  device = "/dev/ttyUSB*" #linux. /dev/ACM* if integrated usb controller (esp32-s2, 32u4)

file_to_upload = sys.argv[1]

#check if there are multiple device with similar port
try:
  o = subprocess.check_output(f"ls {device}",shell=True).decode('utf8')
  print(o)
  if len([d for d in o.split('\n') if len(d)>0])>1:
    device = sys.argv[1]
    file_to_upload = sys.argv[2]
  else:
    print(f"using {device}")
except Exception as e:
  print(e)
  print(f"how to use:\n{sys.argv[0]} [port] (filename to upload)")
  exit(1)
  
  

def upload(filename):
  newfile = f"/tmp/securelemakin_{filename}"
  
  with open(filename) as f:
    with open(newfile,'w') as fw:
      text = python_minifier.minify(f.read(),remove_literal_statements=True)
      fw.write(text)
      print(f"minified to {newfile}")
  cmd = f"pyboard.py -d {device} -f cp {newfile} :{filename}"
  o = subprocess.check_output(cmd,shell=True)
  print(o.decode('utf8'))
  os.unlink(f"{newfile}")

try:
  upload(sys.argv[1])
except Exception as e:
  print(e)
  print(f"how to use:\n{sys.argv[0]} [port] (filename to upload)")

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
  device = "/dev/ttyACM*" #linux. /dev/ACM* if integrated usb controller (esp32-s2, 32u4)

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
  
  
MODE_MPY = 'mpy'
MODE_MIN = 'min'
def upload(filename, mode=MODE_MPY):
  if filename.endswith('.mpy'):
    newfile = filename
  elif filename in ["boot.py","main.py"] or mode==MODE_MIN:
    newfile = f"/tmp/securelemakin_{filename}"
    
    with open(filename) as f:
      with open(newfile,'w') as fw:
        text = python_minifier.minify(f.read(),remove_literal_statements=True)
        fw.write(text)
        print(f"minified to {newfile}")
  elif mode==MODE_MPY and filename.endswith('.py'):
    newfile = f"{filename[:-3]}.mpy"
    cmd = f"mpy-cross {filename}"
    o = subprocess.check_output(cmd,shell=True)
    print(f"compiled to {newfile}")
    filename = newfile
  cmd = f"pyboard.py -d {device} -f cp {newfile} :{filename}"
  o = subprocess.check_output(cmd,shell=True)
  print(o.decode('utf8'))
  if mode==MODE_MPY:
    print(f"removing {newfile}")
    os.unlink(f"{newfile}")
  # ~ os.unlink(f"{newfile}")

try:
  upload(sys.argv[1],sys.argv[2])
except:
  try:
    upload(sys.argv[1])
  except Exception as e:
    print(e)
    print(f"how to use:\n{sys.argv[0]} [port] (filename to upload)")

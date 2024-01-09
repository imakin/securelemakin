#!/usr/bin/env python
import os
import subprocess
import sys


device = '/dev/ttyACM0'
ESP_DIR = '/static'
try:
    subprocess.check_output(f"ls {device}", shell=True)
except subprocess.CalledProcessError as e:
    device = '/dev/tty.usbserial*'
password = None


files = os.listdir('.')
if len(sys.argv)>1:
    files = sys.argv[1:]
for f in files:
    original_name = f
    if f==__name__:
        print(f'skipping {f}')
        continue
    if f.endswith('.js'):
        try:
            cmd = f"uglifyjs {f} > /tmp/{f}.min.js"
            subprocess.check_output(cmd,shell=True)
            f = f'/tmp/{f}.min.js'
            print(cmd)
        except:pass
    cmd = f"pyboard.py --no-soft-reset -d {device} -f cp {f} :{ESP_DIR}/{original_name}"
    print(cmd)
    subprocess.check_output(cmd,shell=True)


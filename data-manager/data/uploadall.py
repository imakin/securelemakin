#!/usr/bin/env python
import os
import subprocess
import sys
sys.path.append('../../esp32s2-double/s2-secure')
import enc


device = '/dev/ttyACM0'
ESP_DIR = '/data'
try:
	subprocess.check_output(f"ls {device}", shell=True)
except subprocess.CalledProcessError as e:
	device = '/dev/tty.usbserial*'
password = None


files = os.listdir('.')
if len(sys.argv)>1:
	files = sys.argv[1:]
for f in files:
	if f.endswith('.py') or f.endswith('.dontupload') or f.endswith('.sh'):
		continue
	if f.endswith('.raw'):
		print(f'encrypting {f}')
		with open(f) as fobj:
			string = fobj.read()
			if string[-1]=='\n':
				string = string[:-1] #remove last empty line
			if password is None:
				print("password used for encryption:")
				password = input()
			m = enc.encrypt(string,password)
			newfilename = f.replace(".raw","")
			with open(newfilename,"wb") as fwrite:
				fwrite.write(m)
				print(f"done making {newfilename}, deleting {f}")
				os.unlink(f)
				f = newfilename
	cmd = f"pyboard.py --no-soft-reset -d {device} -f cp {f} :{ESP_DIR}/{f}"
	print(cmd)
	subprocess.check_output(cmd,shell=True)
	

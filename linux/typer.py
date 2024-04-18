#!/usr/bin/env python3

import os
import subprocess
import sys
import pyautogui
import time
import requests

from flask import Flask, render_template, make_response, Response
from flask.views import View

sys.path.append('../reusable')
import enc
import totp

app = Flask(__name__)

class TyperApp():
    def __init__(self):
        self.DATA_DIR = 'data'
        import secret_masterpassword
        self.pw = secret_masterpassword.get_pw(enc)

    def led(self,on):
        #display indicator, i use keyboard backlight
        if on:
            requests.get('http://127.0.0.1:8090/3')
        else:
            requests.get('http://127.0.0.1:8090/0')
    
    def alert(self,message):
        subprocess.check_call(['notify-send',message])
    
    def auth(self, title=''):
        #auth in my laptop, i use fingerprint
        # os.path.isfile('/usr/bin/fprintd-verify')
        # self.alert(f'fingerprint auth {title}')
        for c in range(1):
            try:
                subprocess.check_call(f'/opt/miniconda/miniconda3/bin/python /home/makin/development/imakingit/SmartHome/facedoor/verify_person.py {os.environ["USER"]}',shell=True)
                return True #break
            except subprocess.CalledProcessError:
                time.sleep(0.5)
                self.alert(f'auth failed {title}')
                pass

        return False


    def read(self,filename,safer=False,noauth=False):
        if not(noauth or self.auth(f'for {filename}')): #equivalent not(noauth) and not(self.auth())
            self.alert('securelemakin auth error')
            return False
        with open(os.path.join(self.DATA_DIR, filename), 'rb') as f:
            cipher = bytearray(f.read())
            m = enc.decrypt(cipher, self.pw)
            if safer:#return as array of utf8 integer
                return [number for number in (m.strip(b'\0'))]
            return (m.strip(b'\0')).decode('utf8')
    
    
    
    def type(self,filename,noauth=False):
        # pyautogui.write(self.read(filename),interval=0.05)
        i = 0
        dt = self.read(filename,safer=True,noauth=noauth)
        try:
            self.led(True)
            if (filename.startswith('otp_')):
                dt = totp.now("".join(chr(c) for c in dt)) #get the TOTP
                dt = [ord(c) for c in dt] #make it array of ord again
            while (i<len(dt)):
                # time.sleep(0.02)
                c = chr(dt[i])
                # print(c)
                try:
                    if c=='\\' and chr(dt[i+1])=='n':
                        pyautogui.press('enter')
                    elif c=='\\' and chr(dt[i+1])=='t':
                        pyautogui.press('tab')
                    else:
                        raise Exception()
                    i += 2
                    continue
                except:pass
                pyautogui.write(c)
                i += 1
        finally:
            self.led(False)

typerapp = TyperApp()

@app.route('/')
@app.route('/<path:filter>')
def file_list(filter=""):
    files = os.listdir('./data')
    files.sort()
    return render_template('file_list_template.html', model={
        "files":files,
        "filter":filter
    })

@app.route('/list/')
def file_list_raw():
    files = os.listdir('./data')
    files.sort()
    return Response(
        "\n".join(files)
        ,status=200
        ,content_type='text/plain'
    )


@app.route('/type/<path:filename>')
def typer_type(filename):
    try:
        typerapp.type(filename)
    finally:
        pass
    return Response("OK", status=200, content_type='text/plain')

if __name__=="__main__":
    # app = TyperApp()
    # pyautogui.write(app.read('bismillah').decode('utf8'),interval=0.05)
    app.run(debug=True)

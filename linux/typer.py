#!/usr/bin/env python3

import os
import subprocess
import sys
# import pyautogui
from pynput.keyboard import Controller  as KeyboardController
from pynput.keyboard import Key as KeyboardKey
import time
import requests

from flask import Flask, render_template, make_response, Response
from flask.views import View

sys.path.append('../reusable')
import enc
import totp

app = Flask(__name__)

class TyperApp():
    def __init__(self,title="server"):
        self.keyboard = KeyboardController()
        print(f"ini{title}")
        self.DATA_DIR = 'data'
        import secret_masterpassword
        self.pw = secret_masterpassword.get_pw(enc,title=title)
        self.last_message = ""

    def led(self,on):
        #display indicator, i use keyboard backlight
        prev_message = self.last_message
        if on:
            self.alert(f"typing...", save_to_last_message=False)
            requests.get('http://127.0.0.1:8090/3')
        else:
            self.alert(f"ready. [{self.last_message}]", save_to_last_message=False)
            requests.get('http://127.0.0.1:8090/0')
    
    def alert(self,message, save_to_last_message=True):
        # subprocess.check_call(['notify-send',message])
        try:
            os.environ["GSETTINGS_SCHEMA_DIR"] = "/home/makin/tweak/gnome/extensions/gnomemakindisplay@izzulmakin/schemas"
            subprocess.check_call(['gsettings','set','com.izzulmakin.gnomemakindisplay','panel-text',f'"{message}"'])
            if save_to_last_message:
                self.last_message = message
        except Exception as e:
            print(e)
            e.print_exc()
    
    def auth(self, title=''):
        #auth in my laptop, i use fingerprint
        # os.path.isfile('/usr/bin/fprintd-verify')
        # self.alert(f'fingerprint auth {title}')
        for c in range(1):
            try:
                d = subprocess.check_output(f'/opt/miniconda/miniconda3/bin/python /home/makin/development/imakingit/SmartHome/facedoor/verify_person_simple.py {os.environ["USER"]}',shell=True)
                d = d.strip().decode('utf8')
                d = f"Izzulmakin: {(200 - int(float(d)))/2}%"
                self.alert(d)
                return True #break
            except subprocess.CalledProcessError:
                time.sleep(0.5)
                d = d.strip().decode('utf8')
                self.alert(f'auth failed {title} {d}')
                pass

        return False


    def read(self,filename,safer=False,noauth=False):
        if not(noauth or self.auth(f'for {filename}')): #equivalent not(noauth) and not(self.auth())
            # self.alert('securelemakin auth error')
            return False
        with open(os.path.join(self.DATA_DIR, filename), 'rb') as f:
            cipher = bytearray(f.read())
            m = enc.decrypt(cipher, self.pw)
            if safer:#return as array of utf8 integer
                return [number for number in (m.strip(b'\0'))]
            return (m.strip(b'\0')).decode('utf8')
    
    
    
    def type(self,filename,noauth=False):
        i = 0
        dt = self.read(filename,safer=True,noauth=noauth)
        if not dt:
            return
        try:
            self.led(True)
            if (filename.startswith('otp_')):
                dt = totp.now("".join(chr(c) for c in dt),on_linux=True) #get the TOTP
                dt = [ord(c) for c in dt] #make it array of ord again
            while (i<len(dt)):
                time.sleep(0.05)
                c = chr(dt[i])
                # print(c)
                try:
                    if c=='\\' and chr(dt[i+1])=='n':
                        # pyautogui.press('enter')
                        self.keyboard.press(KeyboardKey.enter)
                        self.keyboard.release(KeyboardKey.enter)
                    elif c=='\\' and chr(dt[i+1])=='t':
                        # pyautogui.press('tab')
                        self.keyboard.press(KeyboardKey.tab)
                        self.keyboard.release(KeyboardKey.tab)
                    else:
                        raise Exception()
                    i += 2
                    continue
                except:pass
                # pyautogui.write(c)
                self.keyboard.type(c)
                i += 1
        finally:
            self.led(False)

typerapp = None

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
    typerapp = TyperApp()
    app.run(debug=True)

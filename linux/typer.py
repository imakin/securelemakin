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

from multiprocessing import Process,Value, Array


BASEDIR = os.path.dirname(os.path.abspath(__file__))
os.chdir(BASEDIR)

sys.path.append('../reusable')
import enc3
import enc2
import enc
import totp


DATA_DIR = '../data-manager/data-enc3'

app = Flask(__name__)

class IdleChecker(Process):
    MAX_IDLE_TIME = 150 # in seconds
    def __init__(self, flag_should_auth):
        super().__init__()
        self.flag_should_auth = flag_should_auth
    
    def alert(self,message):
        try:
            os.environ["GSETTINGS_SCHEMA_DIR"] = "/home/makin/tweak/gnome/extensions/gnomemakindisplay@izzulmakin/schemas"
            subprocess.check_call(['gsettings','set','com.izzulmakin.gnomemakindisplay','panel-text',f'"{message}"'])
        except Exception as e:
            print(e)
            # e.print_exc()
    
    def run(self):
        while True:
            try:
                time.sleep(-1+self.MAX_IDLE_TIME//2)
                # time.sleep(3)
                idle_time_ms = int(subprocess.check_output(['xprintidle']).strip())
                if idle_time_ms > self.MAX_IDLE_TIME*1000:
                    self.flag_should_auth.value = True
                else:
                    self.flag_should_auth.value = False
                self.alert(f'idle time {idle_time_ms//1000}')
            except:
                self.flag_should_auth.value = True


class TyperApp():
    last_auth_time = 0
    def __init__(self,title="server"):
        self.keyboard = KeyboardController()
        print(f"ini{title}")
        import secret_masterpassword
        self.pw = secret_masterpassword.get_pw(enc3,title=title)
        self.last_message = ""

        self.flag_should_auth = Value('b',True)
        self.idle_checker = IdleChecker(self.flag_should_auth)
        self.idle_checker.daemon = True
        self.idle_checker.start()
        # self.idle_checker.join()

    def led(self,on):
        #display indicator, i use keyboard backlight
        prev_message = self.last_message
        if on:
            self.alert(f"typing...", save_to_last_message=False)
            try:
                requests.get('http://127.0.0.1:8090/3')
            except:pass
        else:
            self.alert(f"ready. [{self.last_message}]", save_to_last_message=False)
            try:
                requests.get('http://127.0.0.1:8090/0')
            except:pass
    
    def alert(self,message, save_to_last_message=True):
        # subprocess.check_call(['notify-send',message])
        try:
            os.environ["GSETTINGS_SCHEMA_DIR"] = "/home/makin/tweak/gnome/extensions/gnomemakindisplay@izzulmakin/schemas"
            subprocess.check_call(['gsettings','set','com.izzulmakin.gnomemakindisplay','panel-text',f'"{message}"'])
            if save_to_last_message:
                self.last_message = message
        except Exception as e:
            print(e)
            # e.print_exc()
    
    
    def auth(self, title=''):
        #auth in my laptop, i use fingerprint
        # os.path.isfile('/usr/bin/fprintd-verify')
        # self.alert(f'fingerprint auth {title}')


        if not self.flag_should_auth.value:
            self.alert('3')
            time.sleep(0.75)
            self.alert('2')
            time.sleep(0.5)
            return True #no need to auth again
        for c in range(1):
            try:
                d = subprocess.check_output(f'/opt/miniconda/miniconda3/bin/python /home/makin/development/imakingit/SmartHome/facedoor/verify_person_simple.py {os.environ["USER"]}',shell=True)
                d = d.strip().decode('utf8')
                d = f"Izzulmakin: {(200 - int(float(d)))/2}%"
                self.alert(d)
                self.last_auth_time = time.time()
                #authenticated
                self.flag_should_auth.value = False
                return True #break
            except subprocess.CalledProcessError:
                time.sleep(0.5)
                try:
                    d = d.strip().decode('utf8')
                except:
                    d = 'err'
                self.alert(f'auth failed {title} {d}')
                pass
        
        #if still failed
        print(f'still failed, try fingerprint')
        tries = 5
        while tries>0:
            try:
                d = subprocess.check_output(['fprintd-verify'])
                return True
            except:
                self.alert(f'fprintd-verify error {tries}')
            tries -= 1

        return False


    def read(self,filename,safer=False,noauth=False):
        if not(noauth or self.auth(f'for {filename}')): #equivalent not(noauth) and not(self.auth())
            # self.alert('securelemakin auth error')
            return False
        with open(os.path.join(DATA_DIR, filename), 'rb') as f:
            cipher = bytearray(f.read())
            m = enc3.decrypt(cipher, self.pw)
            if safer:#return as array of utf8 integer
                return [number for number in (m.strip(b'\0'))]
            return (m.strip(b'\0')).decode('utf8')
    
    
    
    def type(self,filename,noauth=False):
        print(f'os env {os.environ["DISPLAY"]}')
        i = 0
        try:
            dt = self.read(filename,safer=True,noauth=noauth)
        except FileNotFoundError:
            print(f"error. cwd: {os.getcwd()}. file {filename} not found in {DATA_DIR}")
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
                    elif c=='\\' and chr(dt[i+1])=='a':
                        #do a delay
                        try:
                            delay_time = int(chr(dt[i+2]))
                            time.sleep(delay_time)
                            i = i+1 #will become +=2 in the next line
                        except:pass
                    else:
                        raise Exception()
                    i += 2
                    continue
                except Exception as e:
                    pass
                # pyautogui.write(c)
                self.keyboard.type(c)
                i += 1
        except Exception as e:
            print(f'os env {os.environ['DISPLAY']}')
            print(f'ada error: {e}')
        finally:
            self.led(False)

typerapp = None

@app.route('/')
@app.route('/<path:filter>')
def file_list(filter=""):
    files = os.listdir(DATA_DIR)
    files.sort()
    return render_template('file_list_template.html', model={
        "files":files,
        "filter":filter
    })

@app.route('/list/')
def file_list_raw():
    files = os.listdir(DATA_DIR)
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

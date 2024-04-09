from os import listdir
from time import sleep as time_sleep
from time import time as time_time
import socket
import gc

import totp
gc.collect()
import enc
import secret
print(gc.mem_free())
gc.collect()
print(gc.mem_free())
import data_manager
import display
from json import dumps as json_dumps

from machine import (
    Pin,
    unique_id,
    UART,
    # ADC,
    freq
)
from machine import reset as machine_reset
from machine import SoftI2C as I2C
gc.collect()
print(gc.mem_free())

import asymetriclight

freq(160_000_000)

last_printed = ""
def ngeprint(s,force_display=False):
    s = f"{s}"
    global last_printed
    if s!=last_printed:
        last_printed = s
        print(s)
        if force_display==False and display.lock.locked: #respect display lock
            return
        try:
            display.lcd.fill(0)
            line = 0
            while len(s)>0:
                sub = s[:16]
                display.lcd.text(sub,0,line*12,1)
                s = s[16:]
                line += 1
            display.lcd.show()
        except:
            print('[lcd error]')




ledpin = Pin(2,Pin.OUT)
def led(on_or_off):
    if type(on_or_off)==int:
        ledpin.value(1^on_or_off) #bitwise not
    elif type(on_or_off)==bool:
        if on_or_off: ledpin.value(0)
        else: ledpin.value(1)
    elif type(on_or_off)==str and on_or_off=="toggle":
        ledpin.value(1^ledpin.value())


class keyboard(object):
    echo_pin = Pin(37,Pin.OUT)
    @staticmethod
    def on():
        keyboard.echo_pin.value(1)
    @staticmethod
    def off():
        keyboard.echo_pin.value(0)

class CONST:
    PR_BUTTON_MODE = 1
    PR_OK = 0
    PR_ERROR = -1


class Password(object):
    uid = unique_id() #machine.unique_id
    uid_hex = "".join([ ("0"+hex(c)[2:])[-2:] for c in uid])
    password_file = 'master_secret.bin'#contains password, but this password is also encrypted with master_key
    exist = False
    password_passkey = None
    cipher = None


    def __init__(self,enc_context, prime, salt):
        self.enc = enc_context
        uid_hash = self.enc.hashpassword(
            self.uid_hex
            ,prime=prime
            ,salt=salt
        )
        self.password_passkey = "".join([chr(32+(c%(128-32))) for c in uid_hash])
        self.exist = False

    def get(self):
        if self.exist:
            temp = bytearray(self.cipher)
            return self.enc.bytearray_strip(self.enc.decrypt(temp,self.password_passkey))
        else:
            try:
                f = open(self.password_file,'rb')
                self.cipher = bytearray(f.read())
                self.exist = True
                temp = bytearray(self.cipher)
                return self.enc.bytearray_strip(self.enc.decrypt(temp,self.password_passkey))
            except Exception as e:
                self.exist = False
                raise Exception(f'password not set {e}')
            finally:
                try:f.close()
                except:pass


    def set(self,password):
        b = self.enc.encrypt(password,self.password_passkey)
        with open(self.password_file,'wb') as f:
            f.write(b)
            self.cipher = bytearray(b)
            gc.collect()






command_manager = None
class CommandManager(object):
    def __init__(self):
        global command_manager
        if command_manager!=None:
            raise Exception("command_manager singleton already instantiated")
        self.password = Password(enc, secret.Password.prime, secret.Password.salt)
        self.data_keys = data_manager.get_data_keys()
        self.data_pos = 0 #position in self.data_keys for button mode
        self.button_mode_timer = 0

    def set_context(self,ctx):
        self.ctx = ctx

    def singleton(self):
        global command_manager
        if command_manager==None:
            command_manager = CommandManager()
        return command_manager
    
    def cmd_reset(self):
        machine_reset()

    def cmd_print(self,securedata_name,output_mode=False):
        """
        @param output_mode: if True, return output instead of printing to keyboard. 
        return str (not bytes)
        """
        b = bytearray(data_manager.get_data(securedata_name))
        s = enc.bytearray_strip(
            enc.decrypt(b,self.password.get())
        )
        print(s)
        s = s.replace(r'\t','\t') #support escape sequence only for \t and \n
        s = s.replace(r'\n','\n')
        if output_mode:
            return s
        keyboard.on()
        while len(s)>0:
            #dont forget our i2c cant send more than 42 bytes at once
            self.ctx.i2c.writeto(self.ctx.address,s[:32].encode('utf8'))
            s = s[32:]
            time_sleep(1)
        keyboard.off()#s2-keyboard only check pin on the begining of i2c data, so it's safe to off() while s2-keyboard is still receiving
        # ~ time_sleep(0.5)
        self.ctx.i2c.stop()
        print("[OK]")

    def cmd_html_print(self,securedata_name_and_encryptionkey):
        securedata_name,key_n,key_pub = securedata_name_and_encryptionkey.split(' ')
        
        rawoutput = self.cmd_print(securedata_name, output_mode=True)
        chiper = asymetriclight.asyml_enc(rawoutput,int(key_pub),int(key_n))
        self.ctx.html = str(chiper)

    """
    do keyboard ngeprint for chr(char_byte)
    usefull for one key charracter or keyboard like 32 (space) 10 (linefeed) 9(tab)
    """
    def cmd_print_char(self,char_byte):
        if char_byte=="ENTER":
            char_byte = '\n'
        if char_byte=="TAB":
            char_byte = '\t'
        keyboard.on()
        self.ctx.i2c.writeto(self.ctx.address,bytes([ord(char_byte)]))
        time_sleep(0.5)
        keyboard.off()#s2-keyboard only check pin on the begining of i2c data, so it's safe to off() while s2-keyboard is still receiving

    def cmd_sleep(self,seconds_in_byte):
        self.cmd_delay(seconds_in_byte)
    def cmd_delay(self,seconds_in_byte):
        time_sleep(ord(seconds_in_byte))

    def cmd_password(self,password):
        self.password.set(password)

    def cmd_otp(self,securedata_name,output_mode=False):
        #param output_mode: if True, return output instead of printing to keyboard
        b = bytearray(data_manager.get_data(securedata_name))
        s = enc.bytearray_strip(
            enc.decrypt(b,self.password.get())
        )
        pin = totp.now(s)
        if output_mode:
            return pin
        keyboard.on()
        self.ctx.i2c.writeto(self.ctx.address,pin.encode('utf8'))
        time_sleep(0.5)
        keyboard.off()#s2-keyboard only check pin on the begining of i2c data, so it's safe to off() while s2-keyboard is still receiving

    def cmd_html_otp(self,securedata_name_and_encryptionkey):
        securedata_name,key_n,key_pub = securedata_name_and_encryptionkey.split(' ')
        print("CMD HTML OTP",securedata_name,key_n,key_pub)
        securedata_name_and_encryptionkey = None
        gc.collect()
        rawoutput = self.cmd_otp(securedata_name, output_mode=True)
        print("Raw:",rawoutput)
        chiper = asymetriclight.asyml_enc(rawoutput,int(key_pub),int(key_n))
        self.ctx.html = str(chiper)

    def cmd_list(self,nothing):
        files = ";".join(listdir('/data'))
        ngeprint(f"sending to s2-keyboard: {files}")
        self.ctx.html = files
    
    """
    message_and_password is message and password separated by ;;;
    in format:
        [securedataname];;;[message][;;;][password];;;["overwrite"(optional)]
    example:
        mysecretfile;;;my secret string;;;p@55vv0rd                 #will not overwrite
        mysecretfile;;;my secret string;;;p@55vv0rd;;;overwrite     #will overwrite
    """
    def cmd_encrypt(self,message_and_password):
        try:
            data = message_and_password.split(";;;")
            overwrite = False
            if len(data)>4 and data[3]=="overwrite":
                overwrite = True
            else:
                self.data_keys = data_manager.get_data_keys()
                if data[0] in self.data_keys:
                    ngeprint(f"overwrite disabled, and file exist. skipping {data[0]}")
            chip = enc.encrypt(data[1],data[2])
            with open(f"{data_manager.DATA_DIR}/{data[0]}","wb") as f:
                f.write(chip)
                ngeprint("cmd_encrypt [OK]")
        except:
            ngeprint(f"encrypt wrong format {message_and_password} should be 'securedataname;;;my secret string;;;p@55vv0rd;;;overwrite' ")
            pass

    def button_mode(self,message):
        self.button_mode_timer = time_time()
        display.lock.locked = True
        ngeprint(f"buttonmode: {message}")
        if (message=="BB" or message=="l"):
            self.data_pos -= 1
            if self.data_pos<0:
                self.data_pos = len(self.data_keys)-1
        elif message=="BA" or message=="r":
            self.data_pos += 1
            if self.data_pos>=len(self.data_keys):
                self.data_pos = 0
        elif message=="BC" or message=="\n":
            key = self.data_keys[self.data_pos]
            command = "cmd_print"
            if key.startswith("otp_"):
                command = "cmd_otp"
            self.process(f"{command} {key}")
            ngeprint(f"{self.data_keys[self.data_pos]} executed",force_display=True)
            return
                
        ngeprint(self.data_keys[self.data_pos],force_display=True)

    """
    data_message examples:
        "cmd_print securedata_name_secret"
        "cmd_otp mygmail"
        "cmd_password mypassword"
    first word is method in this class
    """
    def process(self,data_message):
        if display.lock.locked and time_time()-self.button_mode_timer>5:
            display.lock.locked = False
        
        if type(data_message) in [bytes,bytearray]:
            m = data_message.decode('utf8')
        elif type(data_message)==str:
            m = data_message
        else:
            raise ValueError("parameter data_message must be str,bytes,or bytearray")
        data_message = None
        gc.collect()
        
        if m in ["BA","BB","BC"]:
            self.button_mode(m)
            return CONST.PR_BUTTON_MODE
        
        try:
            first_space = m.find(' ')
            if first_space<0:
                ngeprint(f"no space, not executed but throws no error {m}")
                return CONST.PR_ERROR
            cmd = m[:first_space]
            param = m[first_space+1:]
            ngeprint(f"(def process) command: {cmd} param: {param}")
            if cmd.startswith('cmd_'):
                getattr(self,cmd)(param)
                ngeprint("[OK]")
                return CONST.PR_OK
            else:
                raise ValueError('malformed...')
        except Exception as e:
            raise e
            # ~ ngeprint(e)
            # ~ raise ValueError(f"malformed data {m}")

class Routine(object):
    def __init__(self):
        self.server = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
        self.server.bind(['',80])
        self.server.listen()
        self.server.settimeout(0.5)
        self.server_last_connection = time_time()

        self.uart = UART(0,baudrate=115200,timeout=500)

        self.address = 100 #s2-keyboard self.address
        self.i2c = I2C(sda=Pin(2),scl=Pin(4),freq=100000)

        sampling = 0

        self.last_wrong_command = b''

        self.command_manager = CommandManager()
        self.command_manager.set_context(self)

        self.html_help = """request example: curl [esp ip address]/[command]/[parameter]"""
        self.html_build()
        self.html = ""


        self.bt_left    = Pin(12,Pin.IN,Pin.PULL_UP)
        self.bt_right   = Pin(35,Pin.IN,Pin.PULL_UP)
        self.bt_ok      = Pin(33,Pin.IN,Pin.PULL_UP)

        def btval():
            if self.bt_ok.value()==0:return '\n'
            if self.bt_left.value()==0:return 'l'
            if self.bt_right.value()==0:return 'r'
            return 1

        ngeprint('securelemakin ready')

        keyboard.off()
        led(1)
        readings = bytearray(256)
        for x in range(len(readings)):readings[x]=0
        while True:
            #button routine
            timer_buttonroutine = time_time()
            while True:
                if btval()!=1:
                    self.command_manager.button_mode(btval())
                    waiting_start = time_time()
                    while btval()!=1:
                        # wait until button released before next loop,
                        #  but if button is held longer than 1s,
                        #  scroll fast
                        if time_time()-waiting_start>1:
                            self.command_manager.button_mode(btval())
                    timer_buttonroutine = time_time()
                
                if (time_time()-timer_buttonroutine)>2:
                    break

            #UART routine
            serialdata = self.uart.read()
            if serialdata:
                ngeprint("routine exit because self.uart is coming")
                ngeprint(serialdata)
                with open("lastdata.bin","wb") as f:
                    f.write(bytearray(serialdata))
                break


            #web server routine
            led("toggle")
            havent_tried = True
            while havent_tried or (time_time()-self.server_last_connection)<1:
                gc.collect()
                havent_tried = False
                try:
                    conn, requesteraddr = self.server.accept()
                except:
                    led("toggle")
                    continue
                self.server_last_connection = time_time()
                led("toggle")
                gc.collect()
                recv = conn.recv(1024)
                try:
                    request_message = recv.decode('utf8')
                    recv = None
                except Exception as e:
                    print(recv)
                    raise e
                if not request_message:
                    continue
                lines = request_message.split('\r\n') #to get the first line
                print("---lines:------")
                print(lines)
                print("---request_message:------")
                print(request_message)
                print("----------")
                if lines and lines[0].startswith('POST'):
                    try:
                        conn, requesteraddr = self.server.accept()
                        conn.sendall(b"HTTP/1.0 200 OK\r\nContent-Type: text/html")
                        print("request again")
                        request_message = conn.recv(1024).decode('utf8')
                        print("2ndrecv---")
                        print(request_message)
                        print("----------")
                    except:
                        print("request again timeout")
                
                elif lines and lines[0].startswith('GET /favicon.ico'):
                    conn.sendall(self.html_favicon())
                    conn.close()
                    request_message = None
                    lines = None
                    gc.collect()
                    continue

                elif lines and lines[0].startswith('GET /static/'):
                    path = lines[0].split(' ')[1].lower()
                    ct = 'text/html'
                    if path.endswith('.js'):
                        ct = 'application/javascript'
                    elif path.endswith('.css'):
                        ct = 'text/css'
                    elif path.endswith('.svg'):
                        ct = 'image/svg+xml'
                    elif path.endswith('.jpg') or path.endswith('.jpeg'):
                        ct = 'image/jpeg'
                    elif path.endswith('.png'):
                        ct = 'image/png'

                    print(f'opening file {path}')
                    try:
                        with open(path) as f:
                            text = f.read()
                            conn.send("HTTP/1.1 200 OK\r\n")
                            conn.send(f"Content-Type: {ct}\r\n")
                            conn.send(f"Content-Length: {len(text)}\r\n\r\n")
                            conn.sendall(text)
                    except:
                        conn.send("HTTP/1.1 404 Not Found\r\n")
                        conn.send(f"Content-Type: text/plain\r\n")
                        conn.send(f"Content-Length: 16\r\n\r\n")
                        conn.send(f"File not found\r\n")
                        
                        
                    conn.close()
                    request_message = None
                    lines = None
                    gc.collect()
                    continue

                path = lines[0].split(' ')[1] #to get the 2nd word from the first line
                commands = path.split('/')
                command = " ".join([word for word in commands if len(word)>0])
                if lines[0].startswith('POST'):
                    lines = 0
                    gc.collect()
                    post_data_start = request_message.find('\r\n\r\n')
                    if post_data_start>=0:
                        command += " "+request_message[post_data_start+4:] #the cmd_* parameter is in POST body
                        print(f"POST executing {command}")
                request_message = None
                lines = None
                path = None
                commands = None
                gc.collect()
                try:
                    if (command.startswith('cmd_print') or command.startswith('cmd_otp')):
                        conn.send("HTTP/1.1 200 OK\r\n")
                        conn.send("Content-Type: text/html\r\n")
                        conn.send("Connection: close\r\n\r\n")
                        conn.send("cmd_print [ok]")
                        conn.sendall(self.html_help)
                        conn.close()
                        time_sleep(2)
                        self.command_manager.process(command)
                        gc.collect()
                        continue
                    else:
                        self.command_manager.process(command)
                except Exception as e:
                    ngeprint(f"wrong command:\n\t{path}\n\t{command}")
                    ngeprint(e)
                
                if (command.startswith('cmd_encrypt')):
                    self.html_build()
                gc.collect()
                

                conn.send("HTTP/1.1 200 OK\r\n")
                conn.send("Content-Type: text/html\r\n")
                conn.send("Connection: close\r\n\r\n")
                if self.html!="":
                    conn.sendall(self.html) #command_manager can update self.html
                else:
                    conn.sendall(self.html_help)
                conn.close()
                self.html = ""
                gc.collect()



    """
    only return the position of the right most non gibberish char
    """
    def bytearray_rstrip_pos(self,buff):
        r = len(buff)-1
        while (r>0 and (buff[r]>=127 or buff[r]==0)):
            r -= 1
        return r

    def bytearray_rstrip(self,buff):
        r = self.bytearray_rstrip_pos(buff)
        return buff[:r+1]
    
    def html_build(self):
        with open('html-help-head.html') as f:
            self.html_help = f.read()
        
        self.html_help += "<script>"
        self.html_help += "let data_command_list = "
        self.html_help += json_dumps(
            {"lis":[
                {
                    "attribute":"",
                    "inner":f
                }
                for f in dir(self.command_manager) if f.startswith('cmd') 
            ]}
        )
        self.html_help += ";\n"

        self.html_help += "let data_data_list = "
        self.html_help += json_dumps(
            {"lis":[
                {
                    "name":f"{sec}",
                    "url":f"/{'cmd_otp' if sec.startswith('otp_') else 'cmd_print'}/{sec}"
                }
                for sec in data_manager.get_data_keys()
            ]}
        )
        self.html_help += ";"
        self.html_help += "</script>"
        

        with open('html-help-ending.html') as f:
            self.html_help += f.read()

    def html_favicon(self):
        #dummy icon http message
        return "HTTP/1.1 200 OK\r\nContent-Type: image/x-icon\r\nContent-Length: 4\r\n\r\n\x89PNG"

try:
    app = Routine()
except KeyboardInterrupt: #so that pyboard --no-soft-reset can do file upload
    led(0)
    ngeprint("s2-keyboard routine exits because of keyboard interrupt")
except MemoryError:
    ngeprint("MEMORY ERROR! press hardware Reset")

import os
import time
import serial
import re

import pyboard


class App():
    def __init__(self, device) -> None:
        self.device = device

    def kirim(self,data,device=None,baud=115200,timeout=1):
        if type(data)==str:
            data = data.encode('utf8')
        print(data)
        if device==None:
            device = self.device
        s = serial.Serial(device,baud,timeout=timeout)
        s.write(data)
        lns = b''
        while True:
            ln = s.readline()
            lns += ln
            if ln:print(ln)
            else:
                print('breaking')
                break
        s.close()
        return lns

    def listdir(self) -> list:
        #pyboard listdir pyboard.filesystem_command(pyb, ['ls','data'])
        #manual list dir
        # self.pyb.enter_raw_repl(soft_reset=False)
        print('ngirim close')
        r = self.kirim(b'\x03')
        r = self.kirim(b'\x03')
        print(r)
        time.sleep(1)
        listdir_text = self.kirim(b'\r\nimport os;os.listdir("data");\r\n')
        # print(listdir_text)
        ls = eval(
            re.findall(r'\[.+?\]', listdir_text.decode('utf8'))[0]
        )
        print('returning ',ls)
        return ls

    def data_esp_to_linux(self):
        files = self.listdir()
        time.sleep(2)
        self.pyb = pyboard.Pyboard(device=self.device)
        self.pyb.enter_raw_repl(False)
        print('pyb ready')
        for f in files:
            print(f'copying {f} to data_esp/{f}')
            pyboard.filesystem_command(
                self.pyb,
                [
                    'cp',
                    f':/data/{f}',
                    f'data_esp/{f}'
                ]
            )
        self.pyb.close()


    def test(self):
        # dt = self.listdir()
        # print(dt)

        self.data_esp_to_linux()

    def merger(self):
        FOLDER = 'data_esp'
        merged = ""
        for fname in os.listdir(FOLDER):
            file = os.path.join(FOLDER,fname)
            with open(file,'rb') as f:
                data = f.read()
                merged = merged + f"{fname}:\n\t{str(data)}\n\n\n"
        with open('datamerged.txt','w') as f:
            f.write(merged)

if __name__=="__main__":
    import sys
    try:
        app = App('/dev/ttyACM0')
        method = getattr(app,sys.argv[1])
        method(*sys.argv[2:])
        # if sys.argv[2:]:
        #     import functools
        #     (functools.partial(method, *sys.argv[2:]))()
    except IndexError:
        pass
        mthd = dir(app)
        print('list of command:')
        [print(f'\t python datamanager.py {m}') for m in mthd if not(m.startswith('__'))]
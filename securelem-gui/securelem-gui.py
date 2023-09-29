#!/usr/bin/env python
import sys
import time
import os
from PySide2.QtWidgets import (
    QApplication
    ,QMainWindow
    ,QWidget
    ,QPushButton
    ,QLineEdit
    ,QLabel
    ,QFileDialog
    ,QFrame
    ,QHBoxLayout
)
from PySide2.QtUiTools import QUiLoader
import serial

#change dir to current executed file (securelem-gui.py)'s directory
os.chdir(os.path.dirname(os.path.abspath(sys.argv[0])))

class MainWindow(QMainWindow):
    def __init__(self):
        super().__init__()
        
        devicename = [d for d in os.listdir('/dev/') if (d.startswith('ttyACM') or d.startswith('tty.usbmodem'))][0]
        self.device = f"/dev/{devicename}"
        self.ser = None

        
        loader = QUiLoader()
        self.ui = loader.load("mainwindow.ui")
        self.setCentralWidget(self.ui)
        self.setWindowTitle("Securelemakin GUI")
        
        self.sc = self.findChild(QWidget, "sc")
        self.le_port = self.findChild(QLineEdit, "le_port")
        self.le_port.setText(self.device)
        
        self.list = {}
        
        with open('securecombo.txt') as f:
            for combo_line in f.read().split('\n'):
                combo_line = combo_line.replace('\n','').replace('\r','')
                self.make_combo(combo_line)
                
        with open('securelist.txt') as f:
            for w in f.read().split(';'):
                name = w.replace('\n','').replace('\r','')
                self.list[name] = {
                    "name":name,
                    "function":None
                }
                self.make_button(name)
        
    
    def serial_open(self):
        try:
            self.ser = serial.Serial(port=self.le_port.text(), baudrate=115200,timeout=3)
            self.le_port.setStyleSheet('background:green')
        except:
            self.le_port.setStyleSheet('background:red')
    def serial_close(self):
        self.ser.close()
    
    def make_button(self,securelem_key):
        bt = QPushButton(self.sc)
        self.sc.layout().addWidget(bt)
        bt.setText(securelem_key)
        def cb():
            if securelem_key.startswith('otp_'):
                self.cmd(securelem_key,'cmd_otp')
            else:
                self.cmd(securelem_key,'cmd_print')
        self.list[securelem_key]["function"] = cb
        bt.clicked.connect(self.list[securelem_key]["function"])
    
    def cmd(self,securelem_key,command="cmd_print"):
        # ~ command = f"cmd_delay {chr(2)}\n{command} {securelem_key}\n"
        time.sleep(1.5)
        command = f"{command} {securelem_key}\n"
        self.serial_open()
        self.ser.write(command.encode('utf8'))
        self.serial_close()
    
    def cmd_tab(self):
        self.serial_open()
        self.ser.write(f"cmd_print_char TAB\n".encode('utf8'))
        self.serial_close()

    def cmd_enter(self):
        self.serial_open()
        self.ser.write(f"cmd_print_char ENTER\n".encode('utf8'))
        self.serial_close()
    def make_combo(self,combo_line):
        securelem_key = f"COMBO: {combo_line.replace(';','-')}"
        self.list[securelem_key] = {}
        self.list[securelem_key]["name"] = securelem_key
        
        bt = QPushButton(self.sc)
        self.sc.layout().addWidget(bt)
        bt.setText(securelem_key)
        def cb():
            for w in combo_line.split(';'):
                print("ex",w)
                if w=="tab":
                    self.cmd_tab()
                elif w=="enter":
                    self.cmd_enter()
                else:
                    self.cmd(w,"cmd_print");
                time.sleep(4)
        self.list[securelem_key]["function"] = cb
        bt.clicked.connect(self.list[securelem_key]["function"])

if __name__ == '__main__':
    app = QApplication(sys.argv)
    window = MainWindow()
    window.show()
    sys.exit(app.exec_())

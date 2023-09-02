#!/usr/bin/env python
import sys
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
        
        self.list = {}
        with open('securelist.txt') as f:
            for w in f.read().split(';'):
                name = w.replace('\n','').replace('\r','')
                self.list[name] = {
                    "name":name,
                    "function":None
                }
                self.make_button(name)
        
        # ~ for key in self.list:
    
    def serial_open(self):
        self.ser = serial.Serial(port=self.device, baudrate=115200,timeout=3)
    def serial_close(self):
        self.ser.close()
    
    def make_button(self,securelem_key):
        bt = QPushButton(self.sc)
        self.sc.layout().addWidget(bt)
        bt.setText(securelem_key)
        def cb():
            self.cmd_print(securelem_key)
        self.list[securelem_key]["function"] = cb
        bt.clicked.connect(self.list[securelem_key]["function"])
    
    def cmd_print(self,securelem_key):
        command = f"cmd_delay {chr(2)}\ncmd_print {securelem_key}\n"
        self.serial_open()
        self.ser.write(command.encode('utf8'))
        self.serial_close()


if __name__ == '__main__':
    app = QApplication(sys.argv)
    window = MainWindow()
    window.show()
    sys.exit(app.exec_())

#!/opt/miniconda/miniconda3/bin/python3
#sending serial with input text gui
import time
import sys
import os
from multiprocessing import Process
import serial

import PySide2.QtWidgets

import serialsender

devicename = [d for d in os.listdir('/dev/') if (d.startswith('ttyACM') or d.startswith('tty.usbmodem'))][0]
device = f"/dev/{devicename}"

serialsender.ser = serial.Serial(port=device, baudrate=115200,timeout=3)

app = PySide2.QtWidgets.QApplication(sys.argv)

le_device = PySide2.QtWidgets.QLineEdit()
le_device.setText(device)

fr = PySide2.QtWidgets.QFrame()
layout = PySide2.QtWidgets.QVBoxLayout(fr)

le = PySide2.QtWidgets.QLineEdit()
# ~ le.setEchoMode(le.Password)
le.setPlaceholderText('message')
layout.addWidget(le)
layout.addWidget(le_device)
def proses():
    p = Process(target=serialsender.kirim, args=(le.text().split(" "),0.4,False,))
    p.daemon = True
    p.start()
    le.hide()
    app.exit(0)
le.returnPressed.connect(proses)

fr.show()
app.exec_()

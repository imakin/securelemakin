from machine import Pin
from machine import SoftI2C as I2C
from time import sleep as time_sleep
import ssd1306

gnd = Pin(3,Pin.OUT)
vcc = Pin(5,Pin.OUT)
scl = Pin(7,Pin.OUT)
sda = Pin(9,Pin.OUT)

#powering, hopefully the display run bellow 20mA
gnd.value(0)
vcc.value(1)
i2c = I2C(sda=sda,scl=scl)
for tries in range(3): #somehow consistently only work after the second try
    try:
        lcd = ssd1306.SSD1306_I2C(128,64,i2c)
        lcd.text("Securelemakin",0,0,1)
        lcd.show()
        break
    except Exception as e:
        print(f'lcd error {e}')
        time_sleep(1)

class Lock:
    def __init__(self):
        self.locked = False

lock = Lock() #display locked flag

from machine import Pin
from machine import SoftI2C as I2C
import ssd1306

# gnd = Pin(13,Pin.OUT)
# vcc = Pin(12,Pin.OUT)
scl = Pin(8,Pin.OUT)
sda = Pin(6,Pin.OUT)

#powering, hopefully the display run bellow 20mA
# gnd.value(0)
# vcc.value(1)
i2c = I2C(sda=sda,scl=scl)
try:
    lcd = ssd1306.SSD1306_I2C(128,64,i2c)
    lcd.text("Securelemakin",0,0,1)
    lcd.show()
except:
    print('lcd error')
class Lock:
    def __init__(self):
        self.locked = False

lock = Lock() #display locked flag

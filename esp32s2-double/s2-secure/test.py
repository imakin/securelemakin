from machine import SoftI2C,Pin
import time
import ssd1306

class Test(object):
    def __init__(self):
        self.i2c = SoftI2C(sda=Pin(2),scl=Pin(3),freq=100000,timeout=200000)
        self.slaveaddress = 100;

    def bacai2c(self):
        txt = b'';
        while True:
            time.sleep(0.1)
            d = self.i2c.readfrom(self.slaveaddress,1)
            txt += d
            if d[0]==0:
                break
        print(txt)

    def oled(self):
        i2c = SoftI2C(scl=Pin(8), sda=Pin(6))
        oled_width = 128
        oled_height = 64
        oled = ssd1306.SSD1306_I2C(oled_width, oled_height, i2c)

        oled.text('Hello', 0, 0)

        oled.show()


t = Test()

from ntptime import settime as ntptime_settime
from time import mktime,localtime
try:
    i2c = securelemakin.display.i2c
except:
    from display import i2c
DS3231_ADDRESS = 0x68

def int2bcd(n):return (n//10)<<4 | (n%10)
def bcd2int(n): return (n>>4)*10 + (n&0x0f)

def calculate_yearday(year, month, date):
    days_in_month = [31,28,31,30,31,30,31,31,30,31,30,31]
    if year % 4 == 0 and (year % 100 != 0 or year % 400 == 0):
        days_in_month[1] = 29
    
    yearday = sum(days_in_month[:month-1]) + date
    return yearday

def lihat():
    data = i2c.readfrom_mem(DS3231_ADDRESS, 0x00, 7)
    print([hex(n) for n in data])
    print(f"{bcd2int(data[2]&0b00111111) + 7}:{bcd2int(data[1])}:{bcd2int(data[0])}")

def rtc_localtime():
    data = i2c.readfrom_mem(DS3231_ADDRESS, 0x00, 7)
    seconds = bcd2int(data[0])
    minutes = bcd2int(data[1])
    hour = bcd2int(data[2]&0b00111111)
    wday = bcd2int(data[3])
    mday = bcd2int(data[4])
    month = bcd2int(data[5])
    year = 2000+bcd2int(data[6])
    yday = calculate_yearday(year, month, mday)
    return (year, month, mday, hour, minutes, seconds, wday, yday)

def read_all():
    data = i2c

#set time
def time_sync():
    ntptime_settime()
    tt = localtime()
    i2c.writeto_mem(DS3231_ADDRESS, 0x00, bytearray([
        int2bcd(tt[5]), #seconds
        int2bcd(tt[4]), #minutes
        int2bcd(tt[3]), #24 hour mode, bit6 is 0
        int2bcd(4), #day
        int2bcd(tt[2]), #date
        int2bcd(tt[1]), #month
        int2bcd(tt[0]%2000), #year
    ]))

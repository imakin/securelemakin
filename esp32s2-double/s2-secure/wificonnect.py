import network
import time
from secret import aplist

wlan = network.WLAN(network.STA_IF) # create station interface
print(f'connected: {wlan.isconnected()}')      # check if the station is connected to an AP
if wlan.isconnected():
    print("wifi already connected")
else:
    wlan.active(True)       # activate the interface
    #wlan.scan()             # scan for access points

    available = wlan.scan()
    print(available)
    for ap in available:
        try:
            ssid = ap[0].decode('utf8')
            pwd = aplist[ssid]
            wlan.connect(ssid,pwd)
            while not wlan.isconnected():pass
            print(f'connected to {ssid}')
            break
        except:
            print(f'cant connect to {ssid}')
    #wlan.config('mac')      # get the interface's MAC address
print(wlan.ifconfig())         # get the interface's IP/netmask/gw/DNS addresses

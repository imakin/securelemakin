import mip
try:
    mip.install("base64")
    mip.install("hmac")
except:
    print('cant install base64 and hmac')
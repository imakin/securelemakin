"""
@author: Izzulmakin
2022
simple encrypt/decrypt readable string with strong padding
Updated 2026: Same strategy but use proper IV randomization
"""
is_micro = True
try:
    #for esp8266 micropython
    import cryptolib
    import gc as garbage_collector
    import urandom.random as urandom
except ModuleNotFoundError:
    #for linux & mac cpython
    print("linux cpython")
    ARCH = 'LINUX'
    is_micro = False
    from Crypto.Cipher import AES #pip install pycryptodome
    from os import urandom
    class cryptolib(object):
        aes = AES.new
import random
import hashlib

import secret #./secret.py

random.seed()

def gc():
    if is_micro:
        garbage_collector.collect()

def randrange(start,stop):
    r = start+(random.getrandbits(32)%(stop-start))
    return r

def empty_block():
    possiblerange_bellow_32 = 32-2
    possiblerange_above_127 = 256-127
    v = random.getrandbits(16)%(possiblerange_bellow_32 + possiblerange_above_127)
    if v==10:
        v+=1
    if v==13:
        v+=1
    if v>=32:
        v += 128-32
    return v

def is_empty_block(v):
    v = int(v)
    if v==10 or v==13:
        return False
    if v>=32 and v<=127:
        return False
    return True

def bytearray_reverse(b):
    front = 0
    back = len(b)-1
    while front<back:
        t = b[front]
        b[front] = b[back]
        b[back] = t
        front += 1
        back -= 1
    return b

def pad(message,max_spread=4):
    try:
        message = message.encode('utf8')
    except AttributeError as e:
        #message is not str
        pass
    message = bytearray(message)

    original_length = len(message)
    temp_length = original_length + (16 - (original_length%16)) + 16
    buff = bytearray(temp_length)
    better_spread = 1+int(temp_length/original_length)
    if better_spread>max_spread:
        max_spread = better_spread
    
    #spread message in random position in buffer, but fill from behind, so reverse message first
    bytearray_reverse(message)
    pb = 0 #position in buffer to write
    pm = 0 #position in message to read
    while pm<original_length:
        max_spread = (len(buff)-pb)//(original_length-pm)
        try:
            spread = randrange(1,max_spread)
        except ZeroDivisionError:
            spread = 1
        pb += spread
        if pb>=len(buff):
            #increase buffer length again
            buff.extend(bytearray(16))
        buff[pb] = message[pm]
        pm+=1
    #refill empty block with padded value
    for pb in range(len(buff)):
        if buff[pb]==0:
            buff[pb] = empty_block()
    #reverse back because message was reversed
    bytearray_reverse(buff)
    return buff

def unpad(message):
    if type(message)!=bytearray:
        raise ValueError("message must be bytearray")

    for p in range(len(message)):
        if is_empty_block(message[p]):
            message[p]=0
    p = 0
    while p<len(message):
        target_non_empty = p
        try:
            while message[target_non_empty]==0:target_non_empty+=1
        except IndexError:
            #no target until ennd of message. all data has been processed
            break
        if p!=target_non_empty:
            message[p] = message[target_non_empty]
            message[target_non_empty] = 0
        p += 1
    return message

def bytearray_strip(message: bytearray)->str:
    r = len(message)-1
    while message[r]==0: r=r-1
    return message[:r+1].decode('utf8')

def hashpassword(password,prime=secret.Hash.prime, salt=secret.Hash.salt):
    h = hashlib.sha256()
    l = len(password)
    password = (salt[:len(salt)//2]+password+salt[len(salt)//2:]).encode('utf8')
    for x in range(l+prime%l):
        h.update(password)
    return h.digest()

"""
@param message: str or byte or bytearray
@param password: str
@return bytearray (IV + ciphertext)
"""
def encrypt(message,password):
    key = hashpassword(password)
    # Generate random IV (16 bytes for AES)
    iv = bytearray(urandom(16))
    encaes = cryptolib.aes(key,2,iv)
    message_padded = pad(message)
    encaes.encrypt(message_padded,message_padded)
    # Prepend IV to ciphertext
    result = iv + message_padded
    encaes,key,iv = None,None,None
    gc()
    return result

"""
@param bytechiper: bytearray (IV + ciphertext), operation done in place to save memory (esp32)
@param password: str
@return bytearray
"""
def decrypt(bytechiper,password):
    if len(bytechiper) < 16:
        raise ValueError("ciphertext too short")
    key = hashpassword(password)
    # Extract IV from first 16 bytes
    iv = bytechiper[:16]
    ciphertext = bytechiper[16:]
    dec = cryptolib.aes(key,2,iv)
    dec.decrypt(ciphertext,ciphertext)
    message = unpad(ciphertext)
    dec,key,iv = None,None,None
    gc()
    return message


if (not is_micro) and __name__=="__main__":
    #test script
    import sys
    verbose = False
    try:
        assert(sys.argv[1]=='-v')
        verbose = True
    except (AssertionError,IndexError): pass
    def printtest(s):
        if verbose: print(s)
    
    # Test padding
    s = "example"
    p1 = pad(s)
    p2 = pad(s)
    printtest(f"{s}\n{p1}\n{p2}")
    try:
        assert(p1!=p2) #different call should result different value
        unpad(p1)
        unpad(p2)
        printtest(f"{s}\n{p1}\n{p2}")
        assert(p1==p2)
        assert(p1.decode('utf8').find(s)==0)
        assert(p2.decode('utf8').find(s)==0)
    except AssertionError as e:
        print(s,p1,p2,sep="\n")
        raise e
    
    # Test encryption/decryption with random IV
    test_message = "Hello, World!"
    password = "testpassword"
    
    encrypted1 = encrypt(test_message, password)
    encrypted2 = encrypt(test_message, password)
    printtest(f"Encrypted 1: {encrypted1[:32]}...")
    printtest(f"Encrypted 2: {encrypted2[:32]}...")
    
    # Different IVs should produce different ciphertexts
    assert(encrypted1 != encrypted2)
    printtest("✓ Different encryptions produce different ciphertexts")
    
    # Both should decrypt to same message
    decrypted1 = decrypt(encrypted1, password)
    decrypted2 = decrypt(encrypted2, password)
    assert(bytearray_strip(decrypted1) == test_message)
    assert(bytearray_strip(decrypted2) == test_message)
    printtest("✓ Both decrypt correctly")
    
    print("All tests passed!")
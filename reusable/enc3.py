"""
@author: Izzulmakin
2026
simple encrypt/decrypt readable string with strong padding
using chacha20 RFC 7539
"""
IS_ESP = True
try:
    #esp32 micropython
    import urandom.random as urandom
    urandom.seed()
except ImportError:
    #linux cpython
    IS_ESP = False
    from os import urandom

from gc import collect as gc_collect
import hashlib

import secret


def random_byte():
    if IS_ESP:
        return urandom.getrandbits(8)
    else:
        return urandom(1)[0]

def random_bytes(n):
    if IS_ESP:
        return bytearray(urandom.getrandbits(8) for _ in range(n))
    else:
        return bytearray(urandom(n))

def randrange(start,stop):
    """
    randomly get number between start to stop-1
    @param start int
    @param stop int (maximum 255)
    """
    r = start+(random_byte()%(stop-start))
    return r

"""
reusable chacha20 implementation
"""
def _rotl32(v, c):
    """Rotate left: 32-bit"""
    return ((v << c) & 0xffffffff) | (v >> (32 - c))

def _quarterround(x, a, b, c, d):
    """ChaCha20 quarter round operation"""
    x[a] = (x[a] + x[b]) & 0xffffffff
    x[d] ^= x[a]
    x[d] = _rotl32(x[d], 16)
    
    x[c] = (x[c] + x[d]) & 0xffffffff
    x[b] ^= x[c]
    x[b] = _rotl32(x[b], 12)
    
    x[a] = (x[a] + x[b]) & 0xffffffff
    x[d] ^= x[a]
    x[d] = _rotl32(x[d], 8)
    
    x[c] = (x[c] + x[d]) & 0xffffffff
    x[b] ^= x[c]
    x[b] = _rotl32(x[b], 7)

def _chacha20_block(key, counter, nonce):
    """Generate a ChaCha20 block (64 bytes)"""
    # Constants "expand 32-byte k"
    state = [
        0x61707865, 0x3320646e, 0x79622d32, 0x6b206574,
        0, 0, 0, 0,  # key[0:4]
        0, 0, 0, 0,  # key[4:8]
        0,           # counter
        0, 0, 0      # nonce[0:3]
    ]
    
    # Fill key (32 bytes = 8 words)
    for i in range(8):
        state[4 + i] = int.from_bytes(key[i*4:(i+1)*4], 'little')
    
    # Fill counter (1 word)
    state[12] = counter
    
    # Fill nonce (12 bytes = 3 words)
    for i in range(3):
        state[13 + i] = int.from_bytes(nonce[i*4:(i+1)*4], 'little')
    
    # Copy initial state
    working_state = state[:]
    
    # 20 rounds (10 double rounds)
    for _ in range(10):
        # Column rounds
        _quarterround(working_state, 0, 4, 8, 12)
        _quarterround(working_state, 1, 5, 9, 13)
        _quarterround(working_state, 2, 6, 10, 14)
        _quarterround(working_state, 3, 7, 11, 15)
        # Diagonal rounds
        _quarterround(working_state, 0, 5, 10, 15)
        _quarterround(working_state, 1, 6, 11, 12)
        _quarterround(working_state, 2, 7, 8, 13)
        _quarterround(working_state, 3, 4, 9, 14)
    
    # Add initial state
    for i in range(16):
        working_state[i] = (working_state[i] + state[i]) & 0xffffffff
    
    # Serialize to bytes
    output = bytearray(64)
    for i in range(16):
        output[i*4:(i+1)*4] = working_state[i].to_bytes(4, 'little')
    
    return output

class ChaCha20:
    """ChaCha20 stream cipher"""
    
    def __init__(self, key, nonce, counter=0):
        """
        Initialize ChaCha20
        key: 32 bytes
        nonce: 12 bytes (96-bit nonce for RFC 7539)
        counter: initial block counter (default 0, RFC 7539 test uses 1)
        """
        if len(key) != 32:
            raise ValueError("Key must be 32 bytes")
        if len(nonce) != 12:
            raise ValueError("Nonce must be 12 bytes")
        
        self.key = bytes(key)
        self.nonce = bytes(nonce)
        self.counter = counter  # Block counter (increments for each 64-byte block)
    
    def _generate_keystream(self, length):
        """Generate keystream of specified length (more efficient than byte-by-byte)"""
        keystream = bytearray()
        blocks_needed = (length + 63) // 64  # Ceiling division
        
        for _ in range(blocks_needed):
            block = _chacha20_block(self.key, self.counter, self.nonce)
            keystream.extend(block)
            self.counter += 1
        
        return keystream[:length]
    
    def encrypt(self, plaintext):
        """Encrypt plaintext (or decrypt ciphertext - same operation)"""
        if isinstance(plaintext, str):
            plaintext = plaintext.encode('utf8')
        
        # Generate keystream for entire message (much faster than byte-by-byte)
        keystream = self._generate_keystream(len(plaintext))
        
        output = bytearray(len(plaintext))
        for i in range(len(plaintext)):
            output[i] = plaintext[i] ^ keystream[i]
        
        return output
    
    def reset(self):
        """Reset counter to 0 (useful for reusing cipher with same key/nonce - NOT RECOMMENDED)"""
        self.counter = 0
    
    def decrypt(self, ciphertext):
        """Decrypt ciphertext (same as encrypt for stream cipher)"""
        return self.encrypt(ciphertext)


"""
customized implementation
"""
def empty_block():
    """
    generate random non-readable byte value
        0~32 except 10,13
        and 128~255
    """
    possiblerange_bellow_32 = 32-2
    possiblerange_above_127 = 256-127
    v16 = random_byte()<<8 | random_byte()
    v = v16%(possiblerange_bellow_32 + possiblerange_above_127)
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
    """
    hash password with sha256
    used for chacha20 key (32bytes)
    
    :param password: str password
    :param prime: prime number 
    :param salt: str salt value
    :return: hashed password bytes
    """
    h = hashlib.sha256()
    l = len(password)
    password = (salt[:len(salt)//2]+password+salt[len(salt)//2:]).encode('utf8')
    for x in range(l+prime%l):
        h.update(password)
    return h.digest() #32bytes

def encrypt(message,password):
    key = hashpassword(password)
    # Generate random IV (16 bytes for AES)
    nonce = random_bytes(12)
    cipher = ChaCha20(key, nonce)
    message_padded = pad(message)
    bytearray_output = (
        nonce + cipher.encrypt(message_padded)
    )

    key,nonce,cipher,message_padded = None,None,None,None
    gc_collect()
    
    return bytearray_output

def decrypt(ciphertext,password, strip=False):
    """
    decrypt ciphertext with password
    
    :param ciphertext: bytearray (IV + ciphertext)
    :param password: str password
    :param strip: if True, will strip null suffix and return str 
        using bytearray_strip()
    :return: bytearray or str (if strip=True)
    """
    key = hashpassword(password)
    nonce = ciphertext[:12]
    cipher = ChaCha20(key, nonce)
    dec = cipher.decrypt(ciphertext[12:])
    message = unpad(dec)
    if strip:
        message = bytearray_strip(message)

    key,nonce,cipher,dec = None,None,None,None
    gc_collect()
    
    return message


print(__name__)


# Compute (base^exp) % modulus using the square-and-multiply algorithm
def modexp(base, exp, modulus, debug=False):
    result = 1
    while exp>0:
        if exp%2==1: #odd number
            result = (result*base) % modulus
            if debug:print(result)
        base = (base*base)%modulus
        exp = exp>>1
        if debug:print(exp)
    return result


def asyml_enc(message,pub,n,hexstring=False):
    try:
        if hexstring:
            return [hex(modexp(ord(c),pub,n)) for c in message]
        return [str(modexp(ord(c),pub,n)) for c in message]
    except:
        return [modexp(c,pub,n) for c in message]

def asyml_dec(chiper,sec,n):
    try:
        if type(chiper[0])==str and chiper[0].startswith('0x'):
            return [chr(modexp(int(c,16),sec,n)) for c in chiper]
        return [chr(modexp(int(c),sec,n)) for c in chiper]
    except:
        return [modexp(int(c),sec,n) for c in chiper]

def test():
    try:
        import keygen
        p = keygen.get_closest_prime(1_600_500_200)
        q = keygen.get_closest_prime(2_300_000_000)
        keys = keygen.generate_keypair(p,q)
    except ImportError:
        keys = ((3681150448298499409, 2702132141316013297), (3681150448298499409, 3077432987023276369))
    print(keys)
    msg = "Bismillah! Makin"
    n = keys[0][0]
    pub = keys[0][1]
    sec = keys[1][1]
    chiper = asyml_enc(msg, pub, n, hexstring=False)
    print(chiper)
    decoded = asyml_dec(chiper, sec, n)
    print("".join(decoded))
    
    
    
    try:
        import keygen
        p = keygen.get_closest_prime(600_500_200)
        q = keygen.get_closest_prime(300_000_000)
        keys = keygen.generate_keypair(p,q)
    except ImportError:
        keys = ((3681150448298499409, 2702132141316013297), (3681150448298499409, 3077432987023276369))
    print(keys)
    msg = "Bismillah! Makin"
    n = keys[0][0]
    pub = keys[0][1]
    sec = keys[1][1]
    chiper = asyml_enc(msg, pub, n, hexstring=False)
    print(chiper)
    decoded = asyml_dec(chiper, sec, n)
    print("".join(decoded))




if __name__=="__main__":
    test()

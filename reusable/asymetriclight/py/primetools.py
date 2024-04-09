"""
@author: Izzulmakin 2023
tools to find prime, using multiprocessing and AVX2 SIMD through numpy 
"""
import os
import sys
import time
from multiprocessing import Process, Queue, Value
import random
from math import gcd
import numpy as np

COMMAND_CLEAR = -1
COMMAND_STOP_ALL_PROCESS = -2


"""
it's the same as check_prime, but with specified factor range to check for multicore threading
check if n has factor of number between start~end
@param start: >=2
@param queue: 
    will be appended a [False] if n has factor
    will be appended a [True] if n has no factor
"""
def find_factor(thread_id, n,start,end,queue,command):
    # ~ print(f"dimulai {n},{start},{end},{queue}")
    starttime = time.time()
    #only check prime_number as factor
    while (start%6)!=0: start+=1
    i = start-6
    while (i<end):
        i += 6
        #checking all number between start~end is fine, but
        #only check prime_number as factor is more efficient;
        #prime number is always 6k-1 or 6k+1, even though not all 6k-1 or 6k+1 is prime
        if (i-1)%6==0 or (i+1)%6==0 or i==2 or i==3:
            pass # (i) is probably prime number, check if (i) is factor of (n)
        else :
            #   (i) is not (6k-1 or 6k+1).
            # it means 2 or 3 is factor of (i)
            # reaching here means (2) or (3) is not factor of (n)
            # then (i) which is multiply of (2) or (3) must not be factor of (n)
            continue 

        # ~ if i%100==0:print(f"comparing {i}")
        if command.value==thread_id: #command.value equals current thread_id, means in attended prime search, the user wants to know current status
            elapsed = time.time()
            print(f"from thread #{thread_id}")
            print(f"progress: {i} percent: {100*(i-start)/(end-start)}%")
            print(f"elapsed: {elapsed-starttime}")
            print(f"speed: {(i-start)/(elapsed-starttime)} item/second")
            
            with command.get_lock():
                command.value = COMMAND_CLEAR #clear
        if n%i==0 or command.value==COMMAND_STOP_ALL_PROCESS:
            with command.get_lock():
                command.value = COMMAND_STOP_ALL_PROCESS
            queue.put(False)
            break
            
    #if all potential factor is checked and none found, and taking too long,
    #it's intersting to know the speed
    elapsed = time.time()
    if (elapsed-starttime)>3:
        print(f"elapsed: {elapsed-starttime}")
        print(f"speed: {(end-start)/(elapsed-starttime)} item/second")

    queue.put(True)


def find_factor_simd(thread_id, n, start, end, queue, command):
    starttime = time.time()
    while (start%6)!=0: start+=1

    # Create NumPy arrays for SIMD calculations
    i = np.arange(start, end, 6, dtype=np.int64)
    factors = np.zeros_like(i, dtype=np.bool)

    # SIMD check for potential prime factors
    is_factor = np.logical_or((i - 1) % 6 == 0, (i + 1) % 6 == 0) | (i == 2) | (i == 3)
    factors[is_factor] = True

    # Iterate over potential prime factors
    for idx, factor in enumerate(i):
        if not factors[idx]:
            continue

        # Check factor and handle command interruptions
        if command.value == thread_id:
            elapsed = time.time()
            print(f"from thread #{thread_id}")
            print(f"progress: {factor} percent: {100 * (factor - start) / (end - start)}%")
            print(f"elapsed: {elapsed - starttime}")
            print(f"speed: {(factor - start) / (elapsed - starttime)} item/second")

            with command.get_lock():
                command.value = COMMAND_CLEAR

        if n % factor == 0 or command.value == COMMAND_STOP_ALL_PROCESS:
            with command.get_lock():
                command.value = COMMAND_STOP_ALL_PROCESS
            queue.put(False)
            break

    #if all potential factor is checked and none found, and taking too long,
    #it's intersting to know the speed
    elapsed = time.time()
    if (elapsed-starttime)>3:
        print(f"elapsed: {elapsed-starttime}")
        print(f"speed: {(end-start)/(elapsed-starttime)} item/second")

    queue.put(True)


def check_prime(v,numthreads=4,unattended=True,simd=True):
    if (v-1)%6==0 or (v+1)%6==0:
        pass
    else:
        return False
    if v<2:
        return False
    q = Queue()
    command = Value('i',COMMAND_CLEAR)
    threads = []
    part_start = 2
    part_end = 2
    try:
        search_limit = round(v**0.5)+1 #checking prime only need to find factor bellow squareroot of (v)
    except TypeError:
        print(f"error here with v = {v}")
        exit(1)
    for t in range(numthreads): #separate search_limit into #numthreads
        part_start = part_end
        part_end = search_limit*(t+1)//numthreads
        _find_factor = (find_factor_simd if simd else find_factor)
        t = Process(target=_find_factor, args=(t, v, part_start, part_end, q, command, ), daemon=True)
        t.start()
        threads.append(t)
    
    line = ""
    # ~ print (f"sampai sini {v} {unattended}")
    while not(unattended):#dont do this if unattended=True
        if line=="exit" or line=="x":
            print("force exit")
            break
        if line.isnumeric():
            thread_id = int(line)
            with command.get_lock():
                command.value = thread_id
                print(f"sending command to {thread_id}")
        alldone = True
        for thread in threads:
            if thread.is_alive():
                alldone = False
                break
        if alldone:
            # ~ print("process done.")
            break
        print("enter number of thread_id to check progress, or x to exit")
        line = input()
        

    for thread in threads:
        thread.join()
    
    is_prime = True #assume it is prime
    for t in threads: #expect count if queue equals len(threads)
        try:
            is_prime = q.get(block=True,timeout=0.5)
        except:pass
        if not is_prime:#it is not prime, no need to continue process
            return False
    
    return True #if it reached here, it is prime

"""
get closest prime between (n-3000) and n
"""
def get_closest_prime(n,numthreads=4,unattended=True,simd=True):
    maks = n
    
    for x in range(maks//6,maks//6-500,-1):
        prime = check_prime(6*x-1,numthreads,unattended,simd)
        if prime:
            return 6*x-1
        prime = check_prime(6*x+1,numthreads,unattended,simd)
        if prime:
            return 6*x+1
    return None


if __name__=="__main__":
    print(get_closest_prime(5087293934544))

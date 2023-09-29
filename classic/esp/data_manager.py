from os import listdir,mkdir
from gc import collect as gc_collect
#this file will contain dict variable for secure data. fill it as necessary
#data in get_data(data_name)
#data can be from file in /data folder, make it lazy load to save ram

DATA_DIR = '/data'

try:
    listdir(DATA_DIR)
except OSError:
    mkdir(DATA_DIR)

def get_data_keys()->list:
    return listdir(DATA_DIR)

def get_data(name="")->bytes:
    if name:
        print(f"getting data {name}")
        try:
            f = open(f"{DATA_DIR}/{name}", 'rb')
            buff = f.read()
            f.close()
            f = None
            gc_collect()
            return buff
        except OSError:
            print(f"file not found {name}")
        finally:
            try:f.close()
            except:pass

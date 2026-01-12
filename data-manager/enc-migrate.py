#!/usr/bin/env python
import os
import subprocess
import sys
from pathlib import Path
BASEDIR = os.path.dirname(os.path.abspath(__file__))
os.chdir(BASEDIR)
sys.path.append('../reusable')
import enc
import enc2
import enc3

print("Enter password for decryption:")
password = input()
datadir = Path(BASEDIR)/'data'
enc2dir = Path(BASEDIR)/'data-enc2'
enc2dir.mkdir(exist_ok=True)
enc3dir = Path(BASEDIR)/'data-enc3'
enc3dir.mkdir(exist_ok=True)


def migrate_enc2():
    for f in os.listdir(datadir):
        filepath = datadir
        with open(filepath/f,'rb') as fi:
            data = fi.read()
        try:
            decryptedb = enc.decrypt(bytearray(data),password)
            decrypted = enc.unpad(decryptedb)
            print(f"{f}: {decrypted.decode('utf8')}")

            enc2cryptedb = enc2.encrypt(decrypted,password)
            with open(enc2dir/f,'wb') as fo:
                fo.write(enc2cryptedb)
            print(f"File: {f} re-encrypted with enc2.")
            
        except Exception as e1:
            print(f"File: {f} failed to decrypt with enc: {e1}")

def migrate_enc3():
    for f in os.listdir(datadir):
        filepath = datadir
        with open(filepath/f,'rb') as fi:
            data = fi.read()
        try:
            decryptedb = enc.decrypt(bytearray(data),password)
            decrypted = enc.unpad(decryptedb)
            print(f"{f}: {decrypted.decode('utf8')}")

            enc3cryptedb = enc3.encrypt(decrypted,password)
            with open(enc3dir/f,'wb') as fo:
                fo.write(enc3cryptedb)
            print(f"File: {f} re-encrypted with enc3.")
            
        except Exception as e1:
            print(f"File: {f} failed to decrypt with enc: {e1}")



def get_enc_files(encdir):
    """
    Docstring for get_enc_files
    
    :param encdir: datadir,enc2dir, or enc3dir
    """
    files = {}
    for f in os.listdir(encdir):
        filepath = encdir / f
        files[f] = filepath
    return files


f1 = get_enc_files(datadir)
f2 = get_enc_files(enc2dir)
f3 = get_enc_files(enc3dir)

def rb(file):
    with open(file,'rb') as fi:
        data = fi.read()
    return data

def rbn(name, enc_version):
    if enc_version==1:
        file = f1[name]
    elif enc_version==2:
        file = f2[name]
    elif enc_version==3:
        file = f3[name]
    data = rb(file)
    return data
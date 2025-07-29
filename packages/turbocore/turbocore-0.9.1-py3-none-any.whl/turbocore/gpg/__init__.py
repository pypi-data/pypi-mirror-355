import subprocess
import os
import sys
import turbocore
import hashlib


def sha256_gpg_binary():
    filename = which_gpg()
    h = hashlib.sha256()
    if filename != None:
        with open(filename, 'rb') as f:
            for buffer in iter(lambda: f.read(8192*10), b""):
                h.update(buffer)
            return h.hexdigest()
    return None


def gpg_version():
    if turbocore.this_platform() == "w":
        res = subprocess.check_output('cmd.exe /C "%s" --version' % which_gpg_w(), shell=True, universal_newlines=True)
        return res.replace("\r", "").split("\n")[0].strip()
    if turbocore.this_platform() == "m":
        res = subprocess.check_output('%s --version' % which_gpg_ml(), shell=True, universal_newlines=True)
        return res.replace("\r", "").split("\n")[0].strip()
    if turbocore.this_platform() == "l":
        res = subprocess.check_output('%s --version' % which_gpg_ml(), shell=True, universal_newlines=True)
        return res.replace("\r", "").split("\n")[0].strip()
    return None



def which_gpg_w():
    try:
        res = subprocess.check_output('cmd.exe /C "where gpg"', shell=True, universal_newlines=True)
        res = res.replace("\r", "").strip().split("\n")[0].strip()
        return res
    except:
        return None


def which_gpg_ml():
    try:
        res = subprocess.check_output('/bin/bash -c "which gpg"', shell=True, universal_newlines=True)
        res = res.replace("\r", "").strip().split("\n")[0].strip()
        return res
    except:
        return None


def which_gpg():
    if turbocore.this_platform() == "w":
        return which_gpg_w()
    if turbocore.this_platform() == "m":
        return which_gpg_ml()
    if turbocore.this_platform() == "l":
        return which_gpg_ml()


def main():
    #turbocore.this_sitepackages()
    #    print(which_gpg())
    print(gpg_version())
    print(sha256_gpg_binary())

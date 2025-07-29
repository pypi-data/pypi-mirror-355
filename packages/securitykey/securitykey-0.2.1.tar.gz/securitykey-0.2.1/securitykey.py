import sys
sys.dont_write_bytecode = True

import random
import string
import json
import os

SKeys = {}

def generateRandomString(length=8):
    return ''.join(random.choices(string.ascii_letters + string.digits, k=length))

def generateKey(keyid="", key="", keyLength=16, idLength=8):
    if not keyid:
        keyid = generateRandomString(idLength)
    if not key:
        key = generateRandomString(keyLength)
    return keyid, key

def storeKey(keyid, key):
    global SKeys
    SKeys[keyid] = key
    saveKeysToFile()

def verifyKey(keyid, some_key):
    return SKeys.get(keyid) == some_key

def _get_store_path():
    if os.name == 'nt':
        return os.path.join(os.getenv('APPDATA'), 'securitykey_SKeys.json')
    else:
        return os.path.expanduser('~/.securitykey_SKeys.json')

def saveKeysToFile():
    path = _get_store_path()
    with open(path, 'w') as f:
        json.dump(SKeys, f, indent=4)

def loadKeysFromFile():
    global SKeys
    path = _get_store_path()
    if os.path.exists(path):
        with open(path, 'r') as f:
            SKeys = json.load(f)

import sys
sys.dont_write_bytecode = True

import random
import string
import json

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
    keys_json = json.dumps(SKeys, indent=4)
    code = f"""import sys
sys.dont_write_bytecode = True

import random
import string
import json

SKeys = {keys_json}

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
    keys_json = json.dumps(SKeys, indent=4)
    with open(__file__, 'w') as f:
        f.write(code)

def verifyKey(keyid, some_key):
    return SKeys.get(keyid) == some_key
"""
    with open(__file__, 'w') as f:
        f.write(code)

def verifyKey(keyid, some_key):
    return SKeys.get(keyid) == some_key

import sys
sys.dont_write_bytecode = True
import random
import string
import json
from cryptography.fernet import Fernet
import os

SKeys = {}
EncryptedHeader = b'ENCRYPTED\n'

def generateRandomString(length=8):
    return ''.join(random.choices(string.ascii_letters + string.digits, k=length))

def generateKey(keyid="", key="", keyLength=128, idLength=8):
    if not keyid:
        keyid = generateRandomString(idLength)
    if not key:
        key = generateRandomString(keyLength)
    return keyid, key

def storeKey(keyid, key):
    global SKeys
    SKeys[keyid] = key
    _saveKeysToFile()

def verifyKey(keyid, some_key):
    return SKeys.get(keyid) == some_key

def _get_store_path():
    if os.name == 'nt':
        return os.path.join(os.getenv('APPDATA'), 'securitykey_SKeys.json')
    else:
        return os.path.expanduser('~/.securitykey_SKeys.json')

def get_encryptionKey_path():
    if os.name == 'nt':
        return os.path.join(os.getenv('APPDATA'), 'encryption.key')
    else:
        return os.path.expanduser('~/.encryption.key')

def generateEncryptionKey():
    key_file = get_encryptionKey_path()
    if not os.path.exists(key_file):
        key = Fernet.generate_key()
        with open(key_file, "wb") as f:
            f.write(key)

def loadEncryptionKey():
    key_file = get_encryptionKey_path()
    with open(key_file, "rb") as f:
        return f.read()

def _saveKeysToFile():
    path = _get_store_path()
    key = loadEncryptionKey()
    fernet = Fernet(key)

    data = json.dumps(SKeys).encode()
    encrypted = fernet.encrypt(data)

    with open(path, "wb") as f:
        f.write(EncryptedHeader + encrypted)

def _loadKeysFromFile():
    global SKeys
    path = _get_store_path()
    if os.path.exists(path):
        with open(path, "rb") as f:
            content = f.read()

        if content.startswith(EncryptedHeader):
            key = loadEncryptionKey()
            fernet = Fernet(key)
            encrypted = content[len(EncryptedHeader):]
            decrypted = fernet.decrypt(encrypted)
            SKeys = json.loads(decrypted.decode())
        else:
            SKeys = json.loads(content.decode())
    else:
        SKeys = {}

generateEncryptionKey()

_loadKeysFromFile()

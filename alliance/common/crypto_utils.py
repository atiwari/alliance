'''
Created on Jul 18, 2014

@author: atiwari
'''

import os
import base64

from Crypto.Cipher import AES
from Crypto.PublicKey import RSA
from Crypto import Random
from Crypto.Signature import PKCS1_v1_5
from Crypto.Hash import SHA256


class AESCrypto(object):

    def __init__(self, conf=None):
        self.block_size = AES.block_size

    def _pad(self, unencrypted):
        """Adds padding to unencrypted byte string."""
        pad_length = self.block_size - (
            len(unencrypted) % self.block_size
        )
        return unencrypted + (chr(pad_length) * pad_length)

    def _strip_pad(self, unencrypted):
        pad_length = ord(unencrypted[-1:])
        unpadded = unencrypted[:-pad_length]
        return unpadded

    def encrypt(self, plain_text, key_dto):
        if not isinstance(plain_text, str):
            raise ValueError('Unencrypted data must be a byte type, '
                             'but was {0}'.format(type(plain_text)))
        padded_data = self._pad(plain_text)
        iv = Random.get_random_bytes(self.block_size)
        encryptor = AES.new(key_dto.key, AES.MODE_CBC, iv)
        cyphertext = iv + encryptor.encrypt(padded_data)
        return cyphertext

    def decrypt(self, cypher_text, key_dto):
        iv = cypher_text[:self.block_size]
        cypher_text = cypher_text[self.block_size:]
        decryptor = AES.new(key_dto.key, AES.MODE_CBC, iv)
        padded_secret = decryptor.decrypt(cypher_text)
        return self._strip_pad(padded_secret)
    
    def generate_key(self, bit_length=128):
        byte_length = int(bit_length) / 8
        unencrypted = os.urandom(byte_length)
        return unencrypted

class RSACrypto(object):
    
    def __init__(self, conf=None):
        pass

    def encrypt(self, plain_text, key_dto):
        with open(key_dto.public_key_file) as f:
            encryptor = RSA.importKey(f.read())
        encrypted_text = encryptor.encrypt(plain_text, 1)
        return "ENC:" + base64.b64encode(encrypted_text[0])

    def decrypt(self, cypher_text, key_dto):
        if cypher_text.startswith("ENC:"):
            cypher_text = cypher_text[4:]
        else:
            return cypher_text

        with open(key_dto.private_key_file) as f:
            decryptor = RSA.importKey(f.read())
        return decryptor.decrypt(base64.b64decode((cypher_text)))

    def sign(self, data, key_dto):
        private_key = open(key_dto.private_key_file, "r").read()
        rsakey = RSA.importKey(private_key)
        signer = PKCS1_v1_5.new(rsakey)
        digest = SHA256.new()
        # Assumes the data is plain 
        digest.update(data)
        signature = signer.sign(digest)
        return base64.b64encode(signature)

    def verify_sign(self, data, signature, key_dto):
        public_key = open(key_dto.public_key_file, "r").read()
        rsakey = RSA.importKey(public_key)
        signer = PKCS1_v1_5.new(rsakey)
        digest = SHA256.new()
        # Assumes the digest is base64 encoded to begin with
        digest.update(data)
        if signer.verify(digest, base64.b64decode(signature)):
            return True
        return False

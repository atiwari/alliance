'''
Created on Jul 18, 2014

@author: atiwari
'''
import base64
import os
from Crypto.PublicKey import RSA
from Crypto import Random
from mock import MagicMock
import testtools

from alliance.common import crypto_utils 
from alliance.common import dtos

class WhenTestingRSACrypto(testtools.TestCase):

    def setUp(self):
        super(WhenTestingRSACrypto, self).setUp()
        self.key_dir = os.path.abspath(os.path.join(os.path.dirname( __file__ ),
                                                    '../../..',
                                                    'etc/keys/self/'))
        self.crypto = crypto_utils.RSACrypto() 
        """
        Note pem encrypted private key with passphrase is not support in pycrypto  
        """
        self.key_dto = dtos.KeyDTO(passphrase='alliance',
                                     public_key_file=os.path.join(self.key_dir,'id_rsa.pub'),
                                     private_key_file=os.path.join(self.key_dir,'id_rsa')) 

    def test_validate_RSA_keys(self):
        self.assertTrue(self.key_dir)
        self.assertTrue(os.path.isfile(self.key_dto.public_key_file))
        self.assertTrue(os.path.isfile(self.key_dto.private_key_file))

        with open(self.key_dto.public_key_file) as f:
            public_key = RSA.importKey(f.read())

        self.assertFalse(public_key.has_private())
        self.assertTrue(public_key.can_encrypt())

        with open(self.key_dto.private_key_file) as f:
            private_key = RSA.importKey(f.read())

        self.assertTrue(private_key.has_private())
        self.assertTrue(private_key.can_sign())
        self.assertTrue(private_key.can_encrypt())
        self.assertEqual(2047, private_key.size())

    def test_RSA_encrypt_decrypt(self):
        text2encrypt = "A quick fox jumped over the lazy dog"
        self.assertEqual(text2encrypt,
                         self.crypto.decrypt(self.crypto.encrypt(text2encrypt, self.key_dto),
                                             self.key_dto))

    def test_RSA_sign_verify(self):
        data2sign = "A quick fox jumped over the lazy dog"
        signature = self.crypto.sign(data2sign, self.key_dto)
        self.assertTrue(self.crypto.verify_sign(data2sign, signature, self.key_dto))


class WhenTestingAESCrypto(testtools.TestCase):

    def setUp(self):
        super(WhenTestingAESCrypto, self).setUp()
        self.crypto = crypto_utils.AESCrypto()
        self.key = 'YWJjZGVmZ2hpamtsbW5vcHFyc3R1dnd4eXoxMjM0NTY='

    def test_generate_256_bit_key(self):
            bit_length = 256
            key = self.crypto.generate_key(bit_length)
            self.assertIsNotNone(key)
            self.assertEqual(len(key), 32)

    def test_generate_256_bit_key_b64(self):
            bit_length = 256
            key = self.crypto.generate_key(bit_length)
            b64e_key = base64.b64encode(key)
            b64d_key = base64.b64decode(b64e_key)
            self.assertEqual(key, b64d_key)
            self.assertEqual(len(b64d_key), 32)
                        
    def test_generate_128_bit_key(self):
            key = self.crypto.generate_key()
            self.assertIsNotNone(key)
            self.assertEqual(len(key), 16)

    def test_pad_binary_string(self):
        binary_string = b'some_binary_string'
        padded_string = (
            b'some_binary_string' +
            b'\x0e\x0e\x0e\x0e\x0e\x0e\x0e\x0e\x0e\x0e\x0e\x0e\x0e\x0e'
        )
        self.assertEqual(self.crypto._pad(binary_string), padded_string)

    def test_pad_random_bytes(self):
        random_bytes = Random.get_random_bytes(10)
        padded_bytes = random_bytes + b'\x06\x06\x06\x06\x06\x06'
        self.assertEqual(self.crypto._pad(random_bytes), padded_bytes)

    def test_strip_padding_from_binary_string(self):
        binary_string = b'some_binary_string'
        padded_string = (
            b'some_binary_string' +
            b'\x0e\x0e\x0e\x0e\x0e\x0e\x0e\x0e\x0e\x0e\x0e\x0e\x0e\x0e'
        )
        self.assertEqual(self.crypto._strip_pad(padded_string), binary_string)

    def test_strip_padding_from_random_bytes(self):
        random_bytes = Random.get_random_bytes(10)
        padded_bytes = random_bytes + b'\x06\x06\x06\x06\x06\x06'
        self.assertEqual(self.crypto._strip_pad(padded_bytes), random_bytes)

    def test_encrypt_unicode_raises_value_error(self):
        unencrypted = u'unicode_beer\U0001F37A'
        self.assertRaises(
            ValueError,
            self.crypto.encrypt,
            unencrypted,
            MagicMock()
        )

    def test_byte_string_encryption(self):
        unencrypted = b'some_secret'
        
        key_dto = dtos.KeyDTO(key=base64.b64decode(self.key))
        cypher_text = self.crypto.encrypt(unencrypted, key_dto)
        decrypted = self.crypto.decrypt(cypher_text, key_dto)
        self.assertEqual(unencrypted, decrypted)
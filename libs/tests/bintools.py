import unittest
import os

import bintools


class BintoolsTests(unittest.TestCase):
    TEST_DIR = os.path.dirname(os.path.realpath(__file__)) + '/test_files'

    def test_hash_file(self):
        file_hash = bintools.hash_file(self.TEST_DIR + '/to_be_hashed')
        file_hash_known = bytes.fromhex('d2ff3650d8809f4622ef8eb1e920710b')

        self.assertEqual(file_hash, file_hash_known)

    def test_decode_object(self):
        obj = {
            "key_one".encode('utf-8'): [
                "value_one".encode('utf-8'),
                "value_two".encode('utf-8'),
                (
                    "value_one".encode('utf-8'),
                    "value_two".encode('utf-8')
                ),
                {
                    "no_decode_key_one".encode('utf-8'): (
                        "me".encode('utf-8'),
                        "you".encode('utf-8')
                    ),
                    "decode_key".encode('utf-8'): "test".encode('utf-8')
                }
            ],
            "no_decode_key_two".encode('utf-8'): "test".encode('utf-8')
        }

        decoded_obj = bintools.decode_object(
            obj,
            encoding='utf-8',
            except_keys=('no_decode_key_one', 'no_decode_key_two')
        )

        self.assertEqual(decoded_obj, {
            "key_one": [
                "value_one",
                "value_two",
                (
                    "value_one",
                    "value_two"
                ),
                {
                    "no_decode_key_one": (
                        "me".encode('utf-8'),
                        "you".encode('utf-8')
                    ),
                    "decode_key": "test"
                }
            ],
            "no_decode_key_two": "test".encode('utf-8')
        })

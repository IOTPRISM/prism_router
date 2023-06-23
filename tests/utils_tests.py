import sys
import unittest
sys.path.append('../')
from utils import *

class UtilsTests(unittest.TestCase):

    def test_is_valid_passphrase(self):
        self.assertFalse(is_valid_passphrase("test"))
        self.assertTrue(is_valid_passphrase("testtest"))
        self.assertFalse(is_valid_passphrase("tes t"))
        self.assertFalse(is_valid_passphrase("ttttttttttttttttttttttttttttttttt"))

    def test_is_valid_ssid(self):
        self.assertFalse(is_valid_ssid("t"))
        self.assertTrue(is_valid_ssid("test"))
        self.assertFalse(is_valid_ssid("ttttttttttttttttttttttttttttttttt"))
    
    def test_is_valid_hex_code(self):
        self.assertTrue(is_valid_hex_code('#e30073'))
        self.assertFalse(is_valid_hex_code('#e300735'))
        self.assertFalse(is_valid_hex_code('e30073'))


if __name__ == '__main__':
    unittest.main()
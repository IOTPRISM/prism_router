import sys
sys.path.append('../')
import unittest
from MacAddress import MacAddress, InvalidMacException

class MacAddressTest(unittest.TestCase):

    def test_incorrect_input(self):
        MacAddress("AA:BB:CC:DD:EE:Ff")
        MacAddress(13)
        MacAddress(2**45)
        with self.assertRaises(InvalidMacException): 
            MacAddress("AA:BB:CC:DD:EE:FG")
        with self.assertRaises(InvalidMacException): 
            MacAddress(-16)
        with self.assertRaises(InvalidMacException): 
            MacAddress(2**56)
        with self.assertRaises(InvalidMacException): 
            MacAddress("00-11-22-33-44-66")
        with self.assertRaises(InvalidMacException): 
            MacAddress("1 2 3 4 5 6 7 8 9 a b c")
        with self.assertRaises(InvalidMacException): 
            MacAddress("This is not a mac")

    def test_mac_string_to_integer(self):
        self.assertEqual(MacAddress("00:00:00:00:00:00").to_int(), 0)
        self.assertEqual(MacAddress("FF:FF:FF:FF:FF:FF").to_int(), 281474976710655)

    def test_mac_integer_to_strign(self):
        self.assertEqual(MacAddress(0).__str__(), "00:00:00:00:00:00")
        self.assertEqual(MacAddress(281474976710655).__str__(), "FF:FF:FF:FF:FF:FF".lower())


if __name__ == '__main__':
    unittest.main()

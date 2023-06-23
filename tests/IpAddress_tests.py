import sys
sys.path.append('../')
import unittest
from IpAddress import IpAddress, InvalidIpv4Exception

class IpAddressTest(unittest.TestCase):

    def test_incorrect_input(self):
        IpAddress("8.8.8.8")
        IpAddress(13)
        IpAddress(2**26)
        with self.assertRaises(InvalidIpv4Exception): 
            IpAddress("test")
        with self.assertRaises(InvalidIpv4Exception): 
            IpAddress(-16)
        with self.assertRaises(InvalidIpv4Exception): 
            IpAddress(2**33)
        with self.assertRaises(InvalidIpv4Exception): 
            IpAddress("FE80::0202:B3FF:FE1E:8329")
        with self.assertRaises(InvalidIpv4Exception): 
            IpAddress("192.156.7.3333")
        with self.assertRaises(InvalidIpv4Exception): 
            IpAddress("This is not a Ip")

    def test_ip_string_to_integer(self):
        self.assertEqual(IpAddress("192.168.0.1").to_int(), 3232235521)
        self.assertEqual(IpAddress("255.255.255.255").to_int(), 2**32 -1)
        self.assertEqual(IpAddress("0.0.0.0").to_int(), 0)

    def test_Ip_integer_to_strign(self):
        self.assertEqual(IpAddress(0).__str__(), "0.0.0.0")
        self.assertEqual(IpAddress(3232235521).__str__(), "192.168.0.1")
        self.assertEqual(IpAddress(2**32 -1).__str__(), "255.255.255.255")


if __name__ == '__main__':
    unittest.main()
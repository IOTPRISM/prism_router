import sys, unittest
sys.path.append('../')
from VendorLookup import VendorLookup
from MacAddress import MacAddress

MAC = MacAddress("00:10:FA:6E:38:4A")

class VendorLookupTest(unittest.TestCase):

    def test_accurate_lookup(self):
        self.assertEqual(VendorLookup().find_vendor(MAC), 'Apple, Inc.')


if __name__ == '__main__':
    unittest.main()
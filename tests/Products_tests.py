import sys
import unittest
from unittest.mock import Mock
sys.path.append('../')
from Products import Products

class ProductsTest(unittest.TestCase):

    def test_load_products(self):
        cur = Mock()
        cur.execute.return_value = [{"name":"test", "vendor": "testVendor"}]
        prods = Products(cur)
        cur.execute.assert_called_once()
        self.assertEqual(prods.products["test"], "testVendor")


    def test_load_blocked(self):
        cur = Mock()
        cur.execute.return_value = [{"name":"test", "vendor": "testVendor"}]
        prods = Products(cur)
        cur.reset_mock()
        cur.execute.return_value = [{"destination":'url1'}, {"destination":'url2'}]
        prods.products = {"test":None}
        prods.load_blocked()
        cur.execute.assert_called_once()
        self.assertEqual(prods.blockedList["test"], ['url1', 'url2'])


if __name__ == '__main__':
    unittest.main()
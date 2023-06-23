import sys, random, string
sys.path.append('../')
import unittest
from Device import Device
from MacAddress import MacAddress
from testing_utils import default_device, random_location, default_location
from unittest.mock import Mock, ANY


class DeviceTestNonDatabaseMethods(unittest.TestCase):


    def test_configure_attributes_product_and_vendor(self):
        d = Device({"product": None,
                    "mac" : MacAddress(6),
                    "user_identified": 0,
                    "auto_identified": 0,
                    "vendor": None,
                    "custom_icon": False})
        self.assertEqual(d.product, 'Unknown')
        self.assertEqual(d.vendor, 'Unknown')

        d = Device({"product": None,
                    "mac" : MacAddress(6),
                    "user_identified": None,
                    "auto_identified": 0,
                    "vendor": "exampleVendor",
                    "custom_icon": False})
        self.assertEqual(d.product, 'Unknown')
        self.assertEqual(d.vendor, 'exampleVendor')

        d = default_device()
        self.assertEqual(d.product, 'exampleProduct')
        self.assertEqual(d.vendor, 'exampleVendor')


    def test_normalise_locations(self):
        d = default_device()
        locations = [random_location() for _ in range(200)]
        d.set_locations(locations)
        largest = max(d.locations, key=lambda l : l.normalised).normalised
        smallest = min(d.locations, key=lambda l : l.normalised).normalised
        self.assertEqual(largest, 0.6)
        self.assertEqual(smallest, 0.1)


    def test_get_locations(self):
        d = default_device()
        locationCount = 50
        locations = [default_location() for _ in range(locationCount)]
        d.set_locations(locations)
        d.set_locations(locations, blocked=True)
        res = [90.0, 180.0, 0.35] * locationCount
        self.assertEqual(d.get_locations(), res)
        self.assertEqual(d.get_locations(blocked=True), res)

    
    def test_get_iso_codes(self):
        isoCodes = [("GB", 10), ("FR", 20), ("US",30)]
        locations = []
        for k, v in isoCodes:
            for _ in range(v):
                l = default_location()
                l.iso_code = k
                locations.append(l)
        d = default_device()
        d.set_locations(locations)
        self.assertEqual(d.get_iso_codes(), isoCodes)
        
    

class TestDeviceSetMethods(unittest.TestCase):


    def test_icon_path_set_correctly(self):
        # test custom_icon False
        d = default_device()
        self.assertEqual(d.icon, f'default-icons/exampleProduct.png')
        # test custom_icon True
        exampleMac = "example_mac"
        d = Device({"product": None,
                    "user_identified": None,
                    "auto_identified": None,
                    "vendor": None,
                    "mac": exampleMac,
                    "custom_icon": True})
        self.assertEqual(d.icon, f'custom-icons/{exampleMac}.png')


    def test_add_custom_icon(self):
        cur = Mock()
        file = Mock()
        d = default_device()
        d.mac = "exampleMac"
        testDir = "testDir/"
        d.add_custom_icon(file, cur, testDir)
        self.assertTrue(d.custom_icon)
        file.save.assert_called_once_with(f"{testDir}custom-icons/exampleMac.png")
        cur.execute.assert_called_once()


    def test_delete_custom_icon(self):
        cur = Mock()
        d = default_device()
        d.mac = "exampleMac"
        with self.assertRaises(FileNotFoundError):
            d.remove_custom_icon(cur, "nonExistingDir/")
        self.assertFalse(d.custom_icon)
        cur.execute.assert_called_once()


    def test_set_user_generated_name_sets_correct_name_with_whitespace_and_capitals(self):
        cur = Mock()
        d = default_device()
        testName = "test Name"
        d.set_name(testName, cur)
        cur.execute.assert_called_once()
        self.assertEqual(d.name, "test-name")


    def test_set_user_generated_name_fails_if_same_name(self):
        cur = Mock()
        d = default_device()
        name = ''.join(random.choice(string.ascii_lowercase) for _ in range(20))
        d.name = name
        d.set_name(name, cur)
        self.assertFalse(cur.execute.called)


    def test_setting_unknown_product_manually_to_unknown_does_nothing(self):
        cur = Mock()
        d = default_device()
        d.product = "Unknown"
        d.set_product("Unknown", cur, False)
        self.assertFalse(d.user_identified)
        cur.execute.assert_not_called()


    def test_setting_unknown_product_manually_works(self):
        cur = Mock()
        d = default_device()
        d.product = "Unknown"
        count = random.randint(0, 50)
        product = ''.join(random.choice(string.ascii_lowercase) for _ in range(20))
        cur.fetchone.return_value = (count, )
        d.set_product(product, cur, False)
        self.assertTrue(d.user_identified)
        self.assertEqual(d.name, f"my-{product}-{count+1}")
        cur.execute.assert_called()


    def test_setting_unknown_product_automatically_works(self):
        cur = Mock()
        d = default_device()
        count = random.randint(0, 50)
        product = ''.join(random.choice(string.ascii_lowercase) for _ in range(20))
        cur.fetchone.return_value = (count, )
        d.set_product(product, cur, True)
        self.assertTrue(d.auto_identified)
        self.assertFalse(d.user_identified)
        self.assertEqual(d.name, f"my-{product}-{count+1}")
        cur.execute.assert_called()


    def test_set_product_fails_if_same_product(self):
        cur = Mock()
        d = default_device()
        d.product = "test-product"
        d.set_product("test-product", cur, False)
        self.assertFalse(cur.execute.called)
        d.set_product("test-product", cur, True)
        self.assertFalse(cur.execute.called)


class TestDeviceBlocking(unittest.TestCase):


    def test_block_domains(self):
        cur = Mock()
        dns = Mock()
        d = default_device()
        d.block_domains("test.com, test2.com, test3.com", cur, dnsOverride=dns)
        cur.execute.assert_any_call(ANY, {"mac": d.mac, "dest": "test.com"})
        cur.execute.assert_any_call(ANY, {"mac": d.mac, "dest": "test2.com"})
        cur.execute.assert_any_call(ANY, {"mac": d.mac, "dest": "test3.com"})
        dns.add.assert_any_call(d.mac, "test.com")
        dns.add.assert_any_call(d.mac, "test2.com")
        dns.add.assert_any_call(d.mac, "test3.com")
        dns.sync.assert_called_once()


    def test_allow_domains(self):
        cur = Mock()
        dns = Mock()
        d = default_device()
        d.allow_domains("test.com, test2.com, test3.com", cur, dnsOverride=dns)
        cur.execute.assert_any_call(ANY, {"mac": d.mac, "dest": "test.com"})
        cur.execute.assert_any_call(ANY, {"mac": d.mac, "dest": "test2.com"})
        cur.execute.assert_any_call(ANY, {"mac": d.mac, "dest": "test3.com"})
        dns.remove.assert_any_call(d.mac, "test.com")
        dns.remove.assert_any_call(d.mac, "test2.com")
        dns.remove.assert_any_call(d.mac, "test3.com")
        dns.sync.assert_called_once()


    def test_set_default_blocking_policy(self):
        cur = Mock()
        d = default_device()
        d.set_default_blocking_policy("block", cur)
        self.assertTrue(d.block_default)
        cur.execute.assert_called_once()
        cur.reset_mock()
        d.set_default_blocking_policy("allow", cur)
        self.assertFalse(d.block_default)
        cur.execute.assert_called_once()
        cur.reset_mock()
        d.set_default_blocking_policy("not-a-command", cur)
        self.assertFalse(d.block_default)
        cur.execute.assert_not_called()


    def test_activate_and_deactivate(self):
        cur = Mock()
        dnsOverride = Mock()
        d = default_device()
        self.assertTrue(d.activated)
        d.deactivate(cur, dnsOverride=dnsOverride)
        cur.execute.assert_called_once()
        dnsOverride.deactivate.assert_called_with(d.mac)
        cur.reset_mock()
        dnsOverride.reset_mock()
        self.assertFalse(d.activated)
        d.activate(cur, dnsOverride=dnsOverride)
        cur.execute.assert_called_once()
        dnsOverride.activate.assert_called_with(d.mac)


if __name__ == '__main__':
    unittest.main()
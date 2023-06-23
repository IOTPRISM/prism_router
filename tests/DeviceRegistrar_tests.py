from ipaddress import ip_address
import sys, unittest
from unittest.mock import Mock, ANY
sys.path.append('../')
from IpAddress import IpAddress
from MacAddress import MacAddress
from DeviceRegistrar import DeviceRegistrar, main
from Database import Database
from testing_utils import initialise_test_database, DB_TEST_FILE

MAC = MacAddress("00:10:FA:6E:38:4A")
IP = IpAddress('192.168.43.1')
HOSTNAME = "device"


class DeviceRegistrarTests(unittest.TestCase):
   
   
    def test_device_is_added_correctly(self):
        db = initialise_test_database(DB_TEST_FILE)
        with db as cur:
            cur.execute("SELECT * FROM device;")
            self.assertIsNone(cur.fetchone())
            dr = DeviceRegistrar(cur)
            dr.register_device(MAC, IP, HOSTNAME)

        with db as cur:
            sqlString = "SELECT mac, ip, hostname FROM device;"
            cur.execute(sqlString)
            self.assertEqual(tuple(cur.fetchone()), (MAC.to_int(), IP.to_int(), HOSTNAME))
            cur.execute(sqlString)
            self.assertEqual(len(cur.fetchmany()), 1)


    def test_vendor_lookup_is_called(self):
        db = initialise_test_database(DB_TEST_FILE)
        v = Mock(return_value="test")
        v.find_vendor.return_value = "test"
        with db as cur:
            dr = DeviceRegistrar(cur, vendorLookup=v)
            dr.register_device(MAC, IP, HOSTNAME)  
        v.find_vendor.assert_called_once_with(MAC)
        

    def test_vendor_lookup_success_is_populated(self):
        db = initialise_test_database(DB_TEST_FILE)
        v = Mock()
        v.find_vendor.return_value = "test"
        with db as cur:
            dr = DeviceRegistrar(cur, v)
            dr.register_device(MAC, IP, HOSTNAME)
        v.find_vendor.assert_called_once_with(MAC)
        sqlString = "SELECT mac_vendor FROM device;"
        with db as cur:
            cur.execute(sqlString)
            self.assertEqual(cur.fetchone()[0], 'test')


    def test_vendor_lookup_failure_is_populated(self):
        db = initialise_test_database(DB_TEST_FILE)
        v = Mock()
        v.find_vendor.return_value = None
        with db as cur:
            dr = DeviceRegistrar(cur, v)
            dr.register_device(MAC, IP, HOSTNAME)
        v.find_vendor.assert_called_once_with(MAC)
        sqlString = "SELECT mac_vendor FROM device;"
        with db as cur:
            cur.execute(sqlString)
            self.assertEqual(cur.fetchone()[0], None)


    def test_adding_existing_device_updates_ip(self):
        cur = Mock()
        v = Mock()
        dc = Mock()
        dc.classify_device.return_value = None
        cur.fetchone.return_value = {"mac":MacAddress(5), "ip":IpAddress(3)}
        DeviceRegistrar(cur, vendorLookup=v, deviceClassifier=dc).register_device(MAC, IP, HOSTNAME)
        cur.execute.assert_called_with(ANY, {"ip":IP, "mac":MAC})


    def test_adding_new_device_updates_ip(self):
        cur = Mock()
        v = Mock()
        dc = Mock()
        dc.classify_device.return_value = None
        cur.fetchone.return_value = False
        DeviceRegistrar(cur, vendorLookup=v, deviceClassifier=dc).register_device(MAC, IP, HOSTNAME)
        sqlString = """ INSERT OR REPLACE INTO device
                        VALUES (?,?,?,?,?,?,?,?,?,?,?,?,?);"""
        cur.execute.assert_called_with(sqlString, ANY)


class DeviceRegistrarMainFunctionTests(unittest.TestCase):

    def test_new_device_is_added_when_main_called(self):
        initialise_test_database(DB_TEST_FILE)
        sys.argv = ["_", MAC.__str__(), IP.__str__(), HOSTNAME]
        db = Database(dbFile=DB_TEST_FILE)
        main(dataBase=db)
        sqlString = "SELECT mac, ip, hostname, mac_vendor FROM device;"
        with db as cur:
            cur.execute(sqlString)
            self.assertEqual(tuple(cur.fetchone()), (MAC.to_int(), IP.to_int(), HOSTNAME, 'Apple, Inc.'))

if __name__ == '__main__':
    unittest.main()

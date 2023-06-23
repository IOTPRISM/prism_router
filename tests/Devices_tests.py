import sys, unittest
from unittest.mock import Mock
from testing_utils import populate_test_database, DB_TEST_FILE
sys.path.append('../')
from Devices import Devices
from Device import Device
from MacAddress import MacAddress
from Database import Database
from custom_errors import UnknownCommandException


class DevicesTest(unittest.TestCase):

    def test_load_devices(self):
        populate_test_database(DB_TEST_FILE)
        with Database(DB_TEST_FILE) as cur:
            devs = Devices(cur, shell=Mock(), network=Mock())
            devs.load_devices()
        self.assertTrue(all(map(lambda k : type(k) == MacAddress, devs.devices.keys())))
        self.assertTrue(all(map(lambda k : type(k) == Device, devs.devices.values())))


    def test_devices_generator(self):
        populate_test_database(DB_TEST_FILE)
        with Database(DB_TEST_FILE) as cur:
            devs = Devices(cur, shell=Mock(), network=Mock())
            devs.load_devices()
        self.assertEqual(len([d for d in devs]), 50)
        self.assertEqual(len(devs), 50)


    def test_update_connected(self):
        populate_test_database(DB_TEST_FILE)
        with Database(DB_TEST_FILE) as cur:
            cur.execute("SELECT mac FROM device;")
            iterator = iter([MacAddress(mac["mac"]).str for mac in cur.fetchall()])
            shellOutput = [ [f"Station {next(iterator)} (on ath0)"],
                            [f"Station {next(iterator)} (on ath1)", f"Station {next(iterator)} (on ath1)"],
                            [f"Station {next(iterator)} (on ath2)" for _ in range(7)] ]
            mockShell = Mock()
            mockNetwork = Mock()
            mockNetwork.wifiInterfaces=["ath0", "ath1", "ath2"]
            mockShell.execute.side_effect=shellOutput
            devs = Devices(cur, shell=mockShell, network=mockNetwork)
            devs.load_devices()
        devs.update_connected()
        self.assertEqual(sum([int(d.connected) for d in devs]), 10) # check 10 devices have connected attr set to true
        mockShell.execute.assert_any_call("iw dev ath0 station dump | grep 'Station'")
        mockShell.execute.assert_any_call("iw dev ath1 station dump | grep 'Station'")
        mockShell.execute.assert_any_call("iw dev ath2 station dump | grep 'Station'")


    def test_load_devices_destinations(self):
        populate_test_database(DB_TEST_FILE)
        with Database(DB_TEST_FILE) as cur:
            devs = Devices(cur, shell=Mock(), network=Mock())
            devs.load_devices()
            devs.load_devices_destinations()
        for d in devs:
            self.assertEqual(len(d.allowedDestinations), 1)
            self.assertEqual(len(d.blockedDestinations), 1)
            self.assertEqual(len(d.queriedDestinations), 2)


    def test_load_devices_locations(self):
        populate_test_database(DB_TEST_FILE)
        with Database(DB_TEST_FILE) as cur:
            devs = Devices(cur, shell=Mock(), network=Mock())
            devs.load_devices()
            devs.load_devices_locations()
        for d in devs:
            self.assertEqual(len(d.locations), 1)
            self.assertEqual(len(d.blockedLocations), 1)
            for l in d.locations:
                self.assertEqual(l.count, 2)
                self.assertEqual(l.normalised, 0.35)
            for l in d.blockedLocations:
                self.assertEqual(l.count, 1)
                self.assertEqual(l.normalised, 0.35)


    def test_load_devices_locations(self):
        populate_test_database(DB_TEST_FILE)
        with Database(DB_TEST_FILE) as cur:
            devs = Devices(cur, shell=Mock(), network=Mock())
            devs.load_devices()
            devs.load_device_metrics()
        for d in devs:
            self.assertEqual(d.totalDestCount, 2)
            self.assertEqual(d.uniqueDestCount, 2)
            self.assertEqual(d.blockedCount, 1)


    def test_enumerate(self):
        populate_test_database(DB_TEST_FILE)
        with Database(DB_TEST_FILE) as cur:
            devs = Devices(cur, shell=Mock(), network=Mock())
            devs.load_devices()
            self.assertEqual(len(devs.enumerate()), 50)
            self.assertEqual(devs.enumerate()[-1][0], 49)
            self.assertEqual(devs.enumerate()[0][0], 0)


    def test_no_data_returns(self):
        populate_test_database(DB_TEST_FILE)
        with Database(DB_TEST_FILE) as cur:
            devs = Devices(cur, shell=Mock(), network=Mock())
            devs.load_devices()
            cur.execute("SELECT mac FROM device ORDER BY mac LIMIT 1;")
            mac = MacAddress(cur.fetchone()["mac"])
            mockDevice = Mock()
            devs.devices[mac] = mockDevice
            devs.set_device_properties(f"{mac}_uploaded", None)
            mockDevice.add_custom_icon.assert_not_called()


    def test_set_name(self):
        populate_test_database(DB_TEST_FILE)
        with Database(DB_TEST_FILE) as cur:
            devs = Devices(cur, shell=Mock(), network=Mock())
            devs.load_devices()
            cur.execute("SELECT mac FROM device ORDER BY mac LIMIT 1;")
            mac = MacAddress(cur.fetchone()["mac"])
            devs.set_device_properties(f"{mac}_new_name", "test-name")
            cur.execute("SELECT name FROM device ORDER BY mac LIMIT 1;")
            self.assertEqual(cur.fetchone()["name"], 'test-name')


    def test_set_product(self):
        populate_test_database(DB_TEST_FILE)
        with Database(DB_TEST_FILE) as cur:
            devs = Devices(cur, shell=Mock(), network=Mock())
            devs.load_devices()
            cur.execute("SELECT mac FROM device ORDER BY mac LIMIT 1;")
            mac = MacAddress(cur.fetchone()["mac"])
            devs.set_device_properties(f"{mac}_new_product", "test-product")
            cur.execute("SELECT product FROM device ORDER BY mac LIMIT 1;")
            self.assertEqual(cur.fetchone()["product"], 'test-product')


    def test_set_custom_icon(self):
        populate_test_database(DB_TEST_FILE)
        with Database(DB_TEST_FILE) as cur:
            devs = Devices(cur, shell=Mock(), network=Mock())
            devs.load_devices()
            cur.execute("SELECT mac FROM device ORDER BY mac LIMIT 1;")
            mac = MacAddress(cur.fetchone()["mac"])
            mockDevice = Mock()
            devs.devices[mac] = mockDevice
            devs.set_device_properties(f"{mac}_uploaded", "file")
            mockDevice.add_custom_icon.assert_called_once()


    def test_delete_icon(self):
        populate_test_database(DB_TEST_FILE)
        with Database(DB_TEST_FILE) as cur:
            devs = Devices(cur, shell=Mock(), network=Mock())
            devs.load_devices()
            cur.execute("SELECT mac FROM device ORDER BY mac LIMIT 1;")
            mac = MacAddress(cur.fetchone()["mac"])
            mockDevice = Mock()
            devs.devices[mac] = mockDevice
            devs.set_device_properties(f"{mac}_delete_icon", "file")
            mockDevice.remove_custom_icon.assert_called_once()


    def test_unknown_command_raises_exception(self):
        populate_test_database(DB_TEST_FILE)
        with Database(DB_TEST_FILE) as cur:
            devs = Devices(cur, shell=Mock(), network=Mock())
            devs.load_devices()
            with self.assertRaises(UnknownCommandException):
                devs.set_device_properties("not-a-command", "random-data")


    def test_delete_device(self):
        populate_test_database(DB_TEST_FILE)
        with Database(DB_TEST_FILE) as cur:
            devs = Devices(cur, shell=Mock(), network=Mock())
            devs.load_devices()
            cur.execute("SELECT mac FROM device ORDER BY mac LIMIT 1;")
            mac = MacAddress(cur.fetchone()["mac"])
            devs.set_device_properties(f"{mac}_delete_device", "random-data")
            with self.assertRaises(KeyError):
                devs.devices[mac]
            cur.execute("SELECT count(*) FROM queried WHERE mac = :mac ;", {"mac":mac})
            self.assertEqual(cur.fetchone()[0], 0)
            cur.execute("SELECT count(*) FROM block_allow WHERE mac = :mac ;", {"mac":mac})
            self.assertEqual(cur.fetchone()[0], 0)


    def test_block_new_domains(self):
        populate_test_database(DB_TEST_FILE)
        with Database(DB_TEST_FILE) as cur:
            devs = Devices(cur, shell=Mock(), network=Mock())
            devs.load_devices()
            cur.execute("SELECT mac FROM device ORDER BY mac LIMIT 1;")
            mac = MacAddress(cur.fetchone()["mac"])
            devs.set_device_properties(f"{mac}_block_domains", "example-block.com")
            cur.execute("SELECT mac, block FROM block_allow WHERE destination = 'example-block.com';")
            result = cur.fetchone()
            self.assertEqual(MacAddress(result[0]), mac)
            self.assertEqual(result[1], 1)


    def test_allow_new_domain(self):
        populate_test_database(DB_TEST_FILE)
        with Database(DB_TEST_FILE) as cur:
            devs = Devices(cur, shell=Mock(), network=Mock())
            devs.load_devices()
            cur.execute("SELECT mac FROM device ORDER BY mac LIMIT 1;")
            mac = MacAddress(cur.fetchone()["mac"])
            devs.set_device_properties(f"{mac}_allow_domains", "example-allow.com")
            cur.execute("SELECT mac, block FROM block_allow WHERE destination = 'example-allow.com';")
            result = cur.fetchone()
            self.assertEqual(MacAddress(result[0]), mac)
            self.assertEqual(result[1], 0)

if __name__ == "__main__":
    unittest.main()

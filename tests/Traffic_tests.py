import sys, unittest
from unittest.mock import Mock
sys.path.append('../')
from testing_utils import populate_test_database, DB_TEST_FILE
from Traffic import Traffic
from Database import Database
from Devices import Devices
from MacAddress import MacAddress


class TrafficTest(unittest.TestCase):


    def test_load_last_day_device_queried_traffic(self):
        populate_test_database(DB_TEST_FILE)
        db = Database(dbFile=DB_TEST_FILE)
        with db as cur:
            devs = Devices(cur, shell=Mock(), network=Mock())
            devs.load_devices()
            traffic = Traffic(cur)
            traffic.load_last_day_device_traffic(devs)
            self.assertEqual(len(traffic.deviceTraffic), 50)
            for k, v in traffic.deviceTraffic.items():
                self.assertEqual(type(k), MacAddress)
                for count in v.values():
                    self.assertEqual(count, 2)



    def test_load_last_day_device_blocked_traffic(self):
        populate_test_database(DB_TEST_FILE)
        db = Database(dbFile=DB_TEST_FILE)
        with db as cur:
            devs = Devices(cur, shell=Mock(), network=Mock())
            devs.load_devices()
            traffic = Traffic(cur)
            traffic.load_last_day_device_traffic(devs)
            self.assertEqual(len(traffic.deviceBlockedTraffic), 50)
            for k, v in traffic.deviceBlockedTraffic.items():
                self.assertEqual(type(k), MacAddress)
                for count in v.values():
                    self.assertEqual(count, 1)


    def test_load_last_day_blocked_traffic_by_type(self):
        populate_test_database(DB_TEST_FILE)
        db = Database(dbFile=DB_TEST_FILE)
        with db as cur:
            devs = Devices(cur, shell=Mock(), network=Mock())
            devs.load_devices()
            traffic = Traffic(cur).blockedByType
            counts = [list(count.values())[0] for count in traffic.values()]
            self.assertEqual(sum(counts), 100)


    def test_load_last_day_allowed_traffic(self):
        populate_test_database(DB_TEST_FILE)
        db = Database(dbFile=DB_TEST_FILE)
        with db as cur:
            devs = Devices(cur, shell=Mock(), network=Mock())
            devs.load_devices()
            traffic = Traffic(cur).allowed
            self.assertEqual((sum(list(traffic.values()))), 50)


if __name__ == "__main__":
    unittest.main()

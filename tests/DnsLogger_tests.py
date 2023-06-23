
import sys
import unittest
from unittest.mock import Mock, ANY
sys.path.append('../')
from DnsLogger import DnsLogger
from Database import Database
from IpAddress import IpAddress
from MacAddress import MacAddress
from Locator import Locator
from custom_errors import DeviceNotInDatabaseError
from testing_utils import populate_dns_log_file, add_device_to_database, initialise_test_database, DB_TEST_FILE

TEST_LOG_FILE = 'dnsmasq.log.test'
MAC = MacAddress("00:10:FA:6E:38:4A")
IP = IpAddress('192.168.43.108')
HOSTNAME = "device"
QUERY = "reddit.com"


class DnsLoggerTests(unittest.TestCase):


    def test_logger_terminates_with_no_interval(self):
        populate_dns_log_file(TEST_LOG_FILE, QUERY, IP)
        add_device_to_database(DB_TEST_FILE, IP, MAC, HOSTNAME)
        db = Database(dbFile=DB_TEST_FILE)
        l = Mock()
        DnsLogger(db, l, dnsLogFile=TEST_LOG_FILE).start(interval=None)


    def test_new_destination_is_identified(self):
        populate_dns_log_file(TEST_LOG_FILE, QUERY, IP)
        initialise_test_database(DB_TEST_FILE)
        add_device_to_database(DB_TEST_FILE, IP, MAC, HOSTNAME)
        db = Database(dbFile=DB_TEST_FILE)
        l = Mock()
        DnsLogger(db, l, dnsLogFile=TEST_LOG_FILE).start(interval=None)
        l.locate_and_save.assert_called_with(QUERY, ANY)


    def test_existing_destination_is_not_identified(self):
        populate_dns_log_file(TEST_LOG_FILE, QUERY, IP)
        initialise_test_database(DB_TEST_FILE)
        add_device_to_database(DB_TEST_FILE, IP, MAC, HOSTNAME)
        db = Database(dbFile=DB_TEST_FILE)
        l = Locator("../maxmind.key")
        DnsLogger(db, l, dnsLogFile=TEST_LOG_FILE).start(interval=None)
        with db as cur:
            cur.execute("SELECT * FROM destination;")
            self.assertEqual(tuple(cur.fetchone()), (QUERY, 'US', 37.751, -97.822, 1, None))
        l = Mock()
        DnsLogger(db, l, dnsLogFile=TEST_LOG_FILE).start(interval=None)
        l.locate_and_save.assert_not_called


    def test_error_raised_when_device_not_in_database(self):
        populate_dns_log_file(TEST_LOG_FILE, QUERY, IP)
        initialise_test_database(DB_TEST_FILE)
        with self.assertRaises(DeviceNotInDatabaseError):
            db = Database(dbFile=DB_TEST_FILE)
            l = Mock()
            DnsLogger(db, l, dnsLogFile=TEST_LOG_FILE).start(interval=None)


if __name__ == "__main__":
    unittest.main()

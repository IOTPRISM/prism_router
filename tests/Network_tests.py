import sys, unittest
from unittest.mock import Mock
sys.path.append('../')
from MacAddress import MacAddress
from IpAddress import IpAddress
from Network import Network

DB_TEST_FILE = 'iotrimmer.db.test'

PROCESSES = ["1192 hostapd -B -P /var/run/ath0_hostapd.pid test_hostap_conf_files/tmp/ath0_hostap.conf.test",
             "1218 hostapd -B -P /var/run/ath1_hostapd.pid test_hostap_conf_files/tmp/ath1_hostap.conf.test",
             "1246 hostapd -B -P /var/run/ath2_hostapd.pid test_hostap_conf_files/tmp/ath2_hostap.conf.test"]

# example of in order output of shell when execute called multiple times during network constructor
CONSTRUCTOR_SHELL_OUTPUT = [
                            ["1.1.1.1 9.9.9.9 8.8.8.8"],
                            ["iotrimmer"],
                            ["192.168.47.1"],
                            ["eth0"],
                            ["    link/ether e8:9f:80:1b:0b:27 brd ff:ff:ff:ff:ff:ff"],
                            ["/tmp/ath0_hostap.conf", "/tmp/ath1_hostap.conf", "/tmp/ath2_hostap.conf"],
                            ["     link/ether e8:9f:80:1b:0b:21 brd ff:ff:ff:ff:ff:ff"],
                            ["     link/ether e8:9f:80:1b:0b:22 brd ff:ff:ff:ff:ff:ff"],
                            ["     link/ether e8:9f:80:1b:0b:23 brd ff:ff:ff:ff:ff:ff"],
                            ["ssid"],
                            ["passphrase"]
                           ]

class NetworkTest(unittest.TestCase):
    
    def test_everything_is_initialised_from_nvram(self):
        mockShell = Mock()
        mockShell.execute.side_effect=CONSTRUCTOR_SHELL_OUTPUT
        network = Network(shell=mockShell)
        self.assertEqual(network.nameServers, [IpAddress("1.1.1.1"), IpAddress("9.9.9.9"), IpAddress("8.8.8.8")])
        self.assertEqual(network.wanInterface, "eth0")
        self.assertEqual(network.wanInterfaceMac, MacAddress("e8:9f:80:1b:0b:27"))
        expected = set([("ath0", MacAddress("e8:9f:80:1b:0b:21")),
                        ("ath1", MacAddress("e8:9f:80:1b:0b:22")),
                        ("ath2", MacAddress("e8:9f:80:1b:0b:23"))])
        self.assertEqual(network.wifiInterfaces, expected)
        self.assertEqual(network.wanInterfaceMac, MacAddress("e8:9f:80:1b:0b:27"))
        self.assertEqual(network.passphrase, "passphrase")
        self.assertEqual(network.ssid, "ssid")
        

    def test_set_ssid_passphrase_are_written_to_nvram(self):
        mockShell = Mock()
        CONSTRUCTOR_SHELL_OUTPUT.extend([[None] for _ in range(6)])
        mockShell.execute.side_effect=CONSTRUCTOR_SHELL_OUTPUT
        network = Network(shell=mockShell)
        network.set_wifi_passphrase("testpass")
        network.set_wifi_ssid("testssid")
        mockShell.execute.assert_any_call("nvram set ath0_ssid=testssid")
        mockShell.execute.assert_any_call("nvram set ath1_ssid=testssid")
        mockShell.execute.assert_any_call("nvram set ath2_ssid=testssid")
        mockShell.execute.assert_any_call("nvram set ath0_wpa_psk=testpass")
        mockShell.execute.assert_any_call("nvram set ath1_wpa_psk=testpass")
        mockShell.execute.assert_any_call("nvram set ath2_wpa_psk=testpass")
        self.assertEqual(mockShell.execute.call_count, 17)   


    def test_invalid_ssid_and_passphrase_are_not_written(self):
        mockShell = Mock()
        CONSTRUCTOR_SHELL_OUTPUT.extend([None for _ in range(6)])
        mockShell.execute.side_effect=CONSTRUCTOR_SHELL_OUTPUT
        network = Network(shell=mockShell)
        network.set_wifi_passphrase("")
        network.set_wifi_ssid("NA")
        self.assertEqual(mockShell.execute.call_count, 11)   


    def test_add_name_servers_and_clear_name_servers_are_written_to_nvram(self):
        mockShell = Mock()
        CONSTRUCTOR_SHELL_OUTPUT.append([None])
        mockShell.execute.side_effect=CONSTRUCTOR_SHELL_OUTPUT
        network = Network(shell=mockShell)
        network.set_name_servers(["4.4.4.4", "8.8.8.8", "9.9.9.9"])
        mockShell.execute.assert_called_with("nvram set wan_dns=4.4.4.4 8.8.8.8 9.9.9.9")
        self.assertEqual(mockShell.execute.call_count, 12)


    def test_invalid_name_server_added(self):
        mockShell = Mock()
        CONSTRUCTOR_SHELL_OUTPUT
        mockShell.execute.side_effect=CONSTRUCTOR_SHELL_OUTPUT
        network = Network(shell=mockShell)
        network.nameServers.clear()
        network.set_name_servers(["not_an_ip"])
        self.assertEqual(mockShell.execute.call_count, 11)


    def test_save_changes_commits_to_nvram(self):
        mockShell = Mock()
        CONSTRUCTOR_SHELL_OUTPUT
        mockShell.execute.side_effect=CONSTRUCTOR_SHELL_OUTPUT
        network = Network(shell=mockShell)
        network.save_changes()
        mockShell.execute.assert_called_with("nvram commit")


if __name__ == "__main__":
    unittest.main()
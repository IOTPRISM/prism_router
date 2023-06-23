import sys, os
sys.path.append('../')
import unittest
from testing_utils import safe_remove
from DnsOverride import DnsConfFile
from MacAddress import MacAddress

MAC = MacAddress("00:10:FA:6E:38:4A")


class DnsConfFileTests(unittest.TestCase):


    def test_new_file_is_created(self):
        file = f"{MAC}_dnsmasq.conf"
        safe_remove(file)
        DnsConfFile(MAC, "./")
        with open(file, 'r') as f:
            self.assertEqual(f.readlines()[0], "bind-interfaces\n")
        safe_remove(file)


    def test_load_domains(self):
        file = f"{MAC}_dnsmasq.conf"
        safe_remove(file)
        DnsConfFile(MAC, "./")
        with open(file, 'a+') as f:
            f.write("address=/example.com/\n")
            f.write("address=/example2.com/\n")
        dcf = DnsConfFile(MAC, "./")
        self.assertEqual(dcf.domains, {"example.com", "example2.com"})
        safe_remove(file)


    def test_listen_addr_and_port(self):
        dcf = DnsConfFile(MAC, "./")
        octets = MAC.__str__().split(':')
        oct2 = str(int(octets[2], 16))
        oct3 = str(int(octets[3], 16))
        oct4 = int(octets[4], 16)
        oct5 = int(octets[5], 16)
        self.assertTrue(oct2 in dcf.listen_addr and oct3 in dcf.listen_addr)
        self.assertEqual(dcf.port - oct4 - oct5, 48620 )


    def test_add_domains(self):
        file = f"{MAC}_dnsmasq.conf"
        safe_remove(file)
        dcf = DnsConfFile(MAC, "./")
        dcf.add_domain("example.com")
        dcf.add_domain("example2.com")
        dcf.add_domain("example3.com")
        dcf.save_domains()
        with open(file, 'r') as f:
            entries = f.readlines()
            self.assertTrue("address=/example3.com/\n" in entries)
            self.assertTrue("address=/example2.com/\n" in entries)
            self.assertTrue("address=/example.com/\n" in entries)
        safe_remove(file)
        

    def test_remove_domains(self):
        file = f"{MAC}_dnsmasq.conf"
        safe_remove(file)
        dcf = DnsConfFile(MAC, "./")
        dcf.add_domain("example.com")
        dcf.add_domain("example3.com")
        dcf.save_domains()
        dcf.remove_domain("example.com")
        dcf.save_domains()
        with open(file, 'r') as f:
            entries = f.readlines()
            self.assertTrue("address=/example3.com/\n" in entries)
            self.assertFalse("address=/example.com/\n" in entries)
        safe_remove(file)
        
        
if __name__ == '__main__':
    unittest.main()
    

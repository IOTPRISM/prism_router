from Database import Database
from MacAddress import MacAddress
from IpAddress import IpAddress
from Device import Device
import sys, sqlite3, logging
from VendorLookup import VendorLookup
from DeviceClassifier import DeviceClassifier
from DnsOverride import DnsOverride


class DeviceRegistrar:

    def __init__(self, cur : sqlite3.Cursor, vendorLookup = VendorLookup(), deviceClassifier = DeviceClassifier()) -> None:
        self.cur = cur
        self.vendorLookup = vendorLookup
        self.deviceClassifier = deviceClassifier


    def register_device(self, mac :MacAddress, ip :IpAddress, hostname = None ) -> None:
        # check device is in database
        self.cur.execute("SELECT mac, ip, deleted FROM device WHERE mac = :mac ; ", {"mac":mac})
        result = self.cur.fetchone()
        
        if not result:
            self._add_new_device(mac, ip, hostname)

        elif result["deleted"]:
            logging.DEBUG(f"Ignoring deleted device with mac :{mac}")
            return

        else:
            origIp = IpAddress(result['ip'])

        if result and origIp != ip:
            self._update_existing_device(mac, ip)
            logging.info(f"Updating device in database from IP address: {origIp} to IP address: {ip}.")

        DnsOverride(self.cur).sync(mac)


    def _update_existing_device(self, mac :MacAddress, ip :IpAddress) -> None:
        sqlString = """ UPDATE device SET 
                            ip = :ip
                        WHERE
                            mac = :mac ;"""
        self.cur.execute(sqlString, {"ip":ip, "mac":mac})


    def _add_new_device(self, mac :MacAddress, ip :IpAddress, hostname :str) -> None:
        # create new device to database
        dev = Device({  "mac": mac,
                        "ip": ip,
                        "hostname": hostname,
                        "vendor": self.vendorLookup.find_vendor(mac)})
        dev.set_name(dev._auto_generate_name(self.cur))
        dev.update_database(self.cur)
        if product := self.deviceClassifier.classify_device(mac, self.cur):
            dev.set_product(product, self.cur, True)
        logging.info(f"Saving new device to database. mac: {mac}, ip: {ip} hostname: {hostname}.")

 
def main(database = None):
    database = Database() if not database else database

    logging.basicConfig(filename='/opt/iotrimmer/logs/deviceRegistrar.log',
                        filemode='a',
                        format='%(asctime)s - %(name)s %(levelname)s %(message)s',
                        datefmt='%H:%M:%S',
                        level=logging.DEBUG)
    try:
        _, mac, ip = sys.argv[:3]
    except ValueError:
        print(f"Script run with arguments: {sys.argv[1:]}")
        print("Script must be called with <mac> <ip> optional:<hostname>")
        print("e.g. 84:8e:0c:71:08:70 192.168.16.191 DanielehsiPhone")
        exit(-1)
    
    try:
        hostname = sys.argv[3]
    except IndexError:
        hostname = None

    with database as cur:
        DeviceRegistrar(cur).register_device(MacAddress(mac), IpAddress(ip), hostname)


if __name__ == "__main__":
    main()

    


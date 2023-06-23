import sqlite3, logging
from Device import Device
from DnsOverride import DnsOverride
from MacAddress import MacAddress
from IpAddress import IpAddress
from utils import flatten_nested_list, get_macs_from_str
from Shell import Shell
from custom_errors import UnknownCommandException, DevicesNotLoadedError
from Locator import Location
from Network import Network


class Devices:


    def __init__(self, cur : sqlite3.Cursor, shell = None, network = None) -> None:
        self.shell = Shell() if not shell else shell
        self.network = Network() if not network else network
        self.cur = cur
        self.destinationsUpdated = {}


    def __iter__(self) -> tuple:
        try:
            return (d for d in sorted(self.devices.values(), key = lambda x: x.name))
        except AttributeError:
            raise DevicesNotLoadedError


    def __len__(self) -> int:
        return len(self.devices)


    def load_devices(self):
        self.devices = {}
        sqlString = """SELECT
                            *
                        FROM
                            device
                        LEFT JOIN
                            product
                        ON
                            device.product = product.name
                        WHERE
                            device.deleted = 0
                        ORDER BY
                            product
                        DESC; """
        for d in self.cur.execute(sqlString):
            dev = Device(dict(d))
            dev.ip = IpAddress(dev.ip)
            dev.mac = MacAddress(dev.mac)
            self.devices[dev.mac] = dev
        return self


    def update_connected(self) -> None:
        macs = []
        for interface in self.network.wifiInterfaces:
            output = self.shell.execute(f"iw dev {interface[0]} station dump | grep 'Station'")
            macs.extend(list(map(get_macs_from_str, output)))
        macs = set(flatten_nested_list(macs))
        for d in self.devices.values():
            d.connected = True if d.mac in macs else False


    def load_devices_destinations(self) -> None:
        for device in self:
            self._find_block_allow_destinations(device)
            self._find_queried_destinations(device)


    def _find_block_allow_destinations(self, device)-> None:
        sqlString = """ SELECT DISTINCT
                            *
                        FROM
                            destination
                        WHERE
                            name IN (   SELECT
                                            destination
                                        FROM 
                                            block_allow
                                        WHERE
                                            mac = :mac
                                        AND
                                            block = :block) ; """

        query = self.cur.execute(sqlString, {"mac":device.mac, "block":1})
        [device.blockedDestinations.append(dict(q)) for q in query]
        query = self.cur.execute(sqlString, {"mac":device.mac, "block":0})
        [device.allowedDestinations.append(dict(q)) for q in query]


    def _find_queried_destinations(self, device : Device)-> None:
        sqlString = """ SELECT DISTINCT
                            *
                        FROM
                            destination
                        WHERE
                            name IN (   SELECT
                                            destination
                                        FROM
                                            queried
                                        WHERE 
                                            mac = :mac); """
        query = self.cur.execute(sqlString, {"mac":device.mac})
        [device.queriedDestinations.append(dict(q)) for q in query]


    def load_devices_locations(self) -> None:
        for device in self:
            self._find_locations(device)
            self._find_blocked_locations(device)


    def _find_locations(self, device : Device) -> None:
        sqlString = """ SELECT
                            count(queried.destination) AS count,
                            latitude,
                            longitude,
                            iso_code
                        FROM
                            destination
                        INNER JOIN
                            queried ON queried.destination = destination.name
                        WHERE
                            queried.mac = :mac
                        AND
                            latitude IS NOT NULL
                        AND
                            longitude IS NOT NULL
                        GROUP BY
                            latitude,
                            longitude,
                            iso_code; """
        locations = map(Location, self.cur.execute(sqlString, {"mac": device.mac}))
        device.set_locations(list(locations), blocked=False)


    def _find_blocked_locations(self, device : Device) -> None:
        sqlString = """ SELECT
                            count(queried.destination) AS count,
                            latitude,
                            longitude,
                            iso_code
                        FROM
                            destination
                        INNER JOIN
                            queried ON queried.destination = destination.name
                        INNER JOIN
                            block_allow ON queried.destination = block_allow.destination
                        AND
                            block_allow.mac = queried.mac
                        WHERE
                            block_allow.mac = :mac
                        AND
                            block_allow.block = 1
                        AND
                            latitude IS NOT NULL
                        AND
                            longitude IS NOT NULL
                        GROUP BY
                            latitude,
                            longitude,
                            iso_code; """
        locations = map(Location, self.cur.execute(sqlString, {"mac": device.mac}))
        device.set_locations(list(locations), blocked=True)


    def load_device_metrics(self) -> None:
        for device in self:
            sqlString = """ SELECT 
                                count(destination),
                                count(DISTINCT destination)
                            FROM 
                                queried
                            WHERE
                                mac = :mac ; """
            self.cur.execute(sqlString, {"mac": device.mac})
            device.totalDestCount, device.uniqueDestCount = self.cur.fetchone()
            sqlString = """ SELECT
                                count(destination)
                            FROM
                                block_allow
                            WHERE  
                                block = 1
                            AND
                                mac = :mac ; """
            self.cur.execute(sqlString, {"mac": device.mac})
            device.blockedCount = self.cur.fetchone()[0]


    def enumerate(self):
        return [(i, d) for i, d in enumerate(self)]


    def set_device_properties(self, command :str, data) -> None:
        print(command, data)
        if not data:
            return
        macs = get_macs_from_str(command)[0]
        d = self.devices[macs]
        if 'new_name' in command:
            d.set_name(data, self.cur)
        elif 'new_product' in command:
            d.set_product(data, self.cur, False)
        elif 'uploaded' in command:
            d.add_custom_icon(data, self.cur)
        elif 'delete_icon' in command:
            d.remove_custom_icon(self.cur)
        elif 'block_domains' in command:
            d.block_domains(data, self.cur)
        elif 'allow_domains' in command:
            d.allow_domains(data, self.cur)
        elif 'set_default_blocking_policy' in command:
            d.set_default_blocking_policy(data, self.cur)
        elif 'delete_device' in command:
            self._delete_device(d)
        else:
            raise UnknownCommandException(command)


    def _delete_device(self, device : Device, dnsOverride = None) -> None:
        dnsOverride = DnsOverride(self.cur) if not dnsOverride else dnsOverride
        sqlStrings = ["UPDATE device SET deleted = 1 WHERE mac = :mac ;",
                      "DELETE FROM queried WHERE mac = :mac ;",
                      "DELETE FROM block_allow WHERE mac = :mac ;"]
        for sqlString in sqlStrings:
            self.cur.execute(sqlString, {"mac": device.mac})
        logging.warning(f"Deleting device: {device.mac}, removing queried, blocked and allowed traffic from database.")
        dnsOverride.deactivate(device.mac)
        self.devices.pop(device.mac)

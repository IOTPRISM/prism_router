from utils import flatten_nested_list
from collections import defaultdict
from DictObj import DictObj
import sqlite3, logging, os
from re import sub
from DnsOverride import DnsOverride
from werkzeug.datastructures import FileStorage
from Locator import Locator


class Device(DictObj):


    def __init__(self, dictionary : dict) -> None:
        # default device parameters
        self.product = None
        self.vendor = None
        self.mac_vendor = None
        self.user_identified = 0
        self.auto_identified = 0
        self.custom_icon = 0
        self.activated = 1
        self.block_default = 0
        self.icon = None
        self.name = None
        super().__init__(dictionary)
        self.locations = []
        self.blockedLocations = []
        self.allowedDestinations = []
        self.blockedDestinations = []
        self.queriedDestinations = []
        self.connected = False
        if not self.product:
            self.product = 'unknown'
        if not self.vendor and not self.mac_vendor:
            self.vendor = 'unknown'
        elif not self.vendor:
            self.vendor = self.mac_vendor
        self._set_icon(self.custom_icon)


    def __str__(self) -> str:
        return "\n".join([f"Device: {self.mac}, {self.ip}", 
                          f"hostname: {self.hostname}",
                          f"vendor: {self.vendor}",
                          f"product: {self.product}",
                          ""])
 

    def update_database(self, cur :sqlite3.Cursor) -> None:
        product = None if self.product == 'unknown' else self.product
        vendor = None if self.vendor == 'unknown' else self.vendor
        # populate all values with current state of object
        sqlString = """ INSERT OR REPLACE INTO device
                        VALUES (?,?,?,?,?,?,?,?,?,?,?,?,?,?);"""
        data = (self.mac,
                self.name,
                self.ip,
                self.hostname,
                product,
                vendor,
                self.user_identified,
                self.auto_identified,
                self.custom_icon,
                self.activated,
                self.block_default,
                self.icon,
                0, # deleted
                self.sniff) # sniff
        cur.execute(sqlString, data)
        logging.debug(f"Updating device with mac: {self.mac} in database.")


    def _set_icon(self, custom :bool, cur = None) -> None:
        self.custom_icon = custom
        if custom:
            self.icon = 'static/custom-icons/' + str(self.mac)
        else: #default
            self.icon ='static/default-icons/' + self.product
        self.icon += '.png'
        if cur:
            self.update_database(cur)
        logging.debug(f"Setting icon for device with mac: {self.mac} to {self.icon}.")


    def remove_custom_icon(self, cur :sqlite3.Cursor) -> None:
        self._set_icon(False, cur)
        if "default-icon" in self.icon:
            return
        filename = "/opt/iotrimmer/" + self.icon
        os.remove(filename)
        logging.info(f"Deleting device icon {self}, deleted from: {filename}")


    def add_custom_icon(self, file :FileStorage, cur :sqlite3.Cursor) -> None:
        self._set_icon(True, cur)
        filename = "/opt/iotrimmer/" + self.icon
        file.save(filename)
        logging.info(f"Updating device icon {self}, saved to: {filename}")


    def set_name(self, newName :str, cur = None) -> None:
        if self.name == newName:
            return
        # replace whitespace with dash
        self.name = sub(r'[^\w]', '-', newName.lower())
        if cur:
            self.update_database(cur)
        logging.info(f"Updating device name of {self}, to: {newName}.")


    def _auto_generate_name(self, cur :sqlite3.Cursor) -> str:
        if self.product == "unknown":
            # count number of unknown devices
            cur.execute(""" SELECT
                                count(*)
                            FROM
                                device
                            WHERE
                                MAX(user_identified, auto_identified) = 0
                            AND
                                device.deleted = 0; """)
            if count := cur.fetchone():
                count = count[0]
            else:
                count = 0
            newName = f"new-device-{count + 1}" 
        else:
            # count devices that are the same product
            sqlString = """ SELECT
                                count(*)
                            FROM
                                device
                            WHERE
                                device.product = (?)
                            AND
                                device.deleted = 0; """
            cur.execute(sqlString, (self.product, ))
            if count := cur.fetchone():
                count = count[0]
            else:
                count = 0
            newName = f"my-{self.product}-{count + 1}"
        logging.debug(f"Auto generated name for device with mac: {self.mac}. Name generated: {newName}.")
        return newName


    def set_product(self, product :str, cur :sqlite3.Cursor, auto :bool, dnsOverride = None) -> None:
        product = product.replace(' ', '-').lower()
        if self.product == product:
            return
        dnsOverride = DnsOverride(cur) if not dnsOverride else dnsOverride
        # remove all blocked locations relating to the old product identification
        self._remove_product_blocked_destinations(cur) 
        # update device table in DB with new type
        known = False if product == "unknown" else True
        if auto:
            self.auto_identified = known
        else:
            self.user_identified = known
        self.product = product
        # add all blocked locations relating to the new product identification
        self._add_product_blocked_destinations(cur)
        # auto-generate name
        autoName = self._auto_generate_name(cur)
        self.set_name(autoName)
        # update icon
        self._set_icon(self.custom_icon)
        self.update_database(cur)
        logging.info(f"Updating device {self} product to {product}.")
        dnsOverride.sync(self.mac)

    
    def toggle_sniff(self, value : bool, cur : sqlite3.Cursor):
        value = int(value)
        if self.sniff == value:
            return
        self.sniff = value
        logging.info(f"Updating device {self} sniff to {'on' if value else 'off'}")
        self.update_database(cur)


    def _remove_product_blocked_destinations(self, cur :sqlite3.Cursor) -> None:
        if self.product == "unknown":
            return 
        sqlString = """ DELETE FROM
                            block_allow
                        WHERE
                            mac = :mac
                        AND
                            destination IN (SELECT
                                                destination
                                            FROM
                                                blocklist
                                            WHERE
                                                product = :product ); """
        data = {"mac": self.mac, "product": self.product}
        cur.execute(sqlString, data)
        logging.info(f"Removing blocked destinations for {self.product} to {self}")


    def _add_product_blocked_destinations(self, cur :sqlite3.Cursor) -> None:
        if self.product == "unknown":
            return 
        sqlString = """ INSERT OR IGNORE INTO
                            block_allow (mac, destination, block)
                        SELECT
                            :mac, destination, 1
                        FROM
                            blocklist
                        WHERE
                            product = :product ; """

        cur.execute(sqlString, {"mac": self.mac, "product": self.product})
        logging.info(f"Adding blocked destinations for {self.product} to {self}")


    def block_domains(self, destinations :list, cur :sqlite3.Cursor, dnsOverride = None, locator = None) -> None:
        dnsOverride = DnsOverride(cur) if not dnsOverride else dnsOverride
        locator = Locator() if not locator else locator
        destinations = destinations.split(',')
        for dest in destinations:
            locator.locate_and_save(dest, cur)
        sqlString = """ INSERT OR REPLACE INTO
                            block_allow (destination, mac, block)
                        VALUES 
                            (:dest, :mac, 1) ; """
        for dest in destinations:
            dest = dest.strip()
            data = {"mac": self.mac, "dest": dest}
            cur.execute(sqlString, data)
        dnsOverride.add(self.mac, destinations)
        dnsOverride.sync(self.mac)


    def allow_domains(self, destinations :list, cur :sqlite3.Cursor, dnsOverride = None, locator = None) -> None:
        dnsOverride = DnsOverride(cur) if not dnsOverride else dnsOverride
        locator = Locator() if not locator else locator
        destinations = destinations.split(',')
        for dest in destinations:
            locator.locate_and_save(dest, cur)
        sqlString = """ INSERT OR REPLACE INTO
                            block_allow (destination, mac, block)
                        VALUES 
                            (:dest, :mac, 0) ; """
        for dest in destinations:
            dest = dest.strip()
            data = {"mac": self.mac, "dest": dest}
            cur.execute(sqlString, data)
        dnsOverride.remove(self.mac, destinations)
        dnsOverride.sync(self.mac)


    def set_default_blocking_policy(self, cmd, cur :sqlite3.Cursor):
        cmd = cmd.lower()
        if cmd not in ["allow", "block"]:
            logging.warning(f"Invalid command received for set default blocking policy for device: {self.mac}")
            return
        block = False if cmd == 'allow' else True
        if self.block_default == block:
            return
        self.block_default = block
        self.update_database(cur)
        logging.info(f"Updating default blocking policy to: {self.block_default} for: {self.mac}")


    def set_locations(self, locations: list, blocked = False) -> None:
        if not locations:
            return
        if blocked:
            self.blockedLocations = self._normalise_locations(locations)
        else:
            self.locations = self._normalise_locations(locations)


    def _normalise_locations(self, locations :list, minV = 0.1, maxV = 0.6) -> list:
        sort_func = lambda l : l.count
        maxL = max(locations, key=sort_func).count # get count of location with highest count
        minL = min(locations, key=sort_func).count # get count of location with lowest count
        return [l.normalise(minL, maxL, minV, maxV) for l in locations]
            

    def get_locations(self, blocked=False) -> list:
        locations = self.blockedLocations if blocked else self.locations
        return flatten_nested_list([l.to_normalised_list() for l in locations])


    def get_iso_codes(self, blocked=False) -> list:
        locations = self.blockedLocations if blocked else self.locations
        data = defaultdict(int)
        for l in locations:
            data[l.iso_code] += l.count
        return [(k, v) for k, v in data.items()]


    def activate(self, cur :sqlite3.Cursor, dnsOverride=None) -> None:
        dnsOverride = DnsOverride(cur) if not dnsOverride else dnsOverride
        if self.activated:
            return
        self.activated = True
        self.update_database(cur)
        dnsOverride.activate(self.mac)
        logging.info(f"Activating DNS filtering for device: {self.mac}")


    def deactivate(self, cur :sqlite3.Cursor, dnsOverride=None) -> None:
        dnsOverride = DnsOverride(cur) if not dnsOverride else dnsOverride
        if not self.activated:
            return
        self.activated = False
        self.update_database(cur)
        dnsOverride.deactivate(self.mac)
        logging.info(f"Deactivating DNS filtering for device: {self.mac}")


    def enumerate_blocked(self) -> list:
        return [(i, url) for i, url in enumerate(sorted(self.blockedDestinations, key = lambda x : x["name"]))]


    def enumerate_allowed(self) -> list:
        # find set of all domains, subtract set of blocked domains, then convert remaining domainsback to DictObj
        allDomains = set([tuple(d.items()) for d in (self.allowedDestinations + self.queriedDestinations)])
        allExceptBlocked = allDomains - set([tuple(d.items()) for d in self.blockedDestinations])
        allExceptBlocked = [DictObj(d) for d in allExceptBlocked]
        return [(i, url) for i, url in enumerate(sorted(allExceptBlocked, key = lambda x : x.name))]


    def print_product(self) -> str:
        return self.product.replace('-', ' ').title()


    def print_vendor(self) -> str:
        return self.vendor.title()

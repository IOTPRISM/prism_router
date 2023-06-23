from sqlite3.dbapi2 import sqlite_version
from Database import Database
import time, logging, sqlite3
from IpAddress import IpAddress, InvalidIpv4Exception
from MacAddress import MacAddress
from datetime import datetime
from Locator import Locator
from Shell import Shell
from os import listdir

TIME_INTERVAL = 30 # seconds
IGNORE = ['localhost', 'dev', 'dyson.ic.ac.uk', 'in-addr.arpa']


class DnsLogger:


    def __init__(self, db : Database, locator : Locator, shell = None, dnsLogDir = "/opt/iotrimmer/dns-override"):
        self.shell = Shell() if not shell else shell
        self.locator = locator
        self.dnsLogDir = dnsLogDir
        self.db = db


    def start(self, interval = None) -> None:
        if interval:
            logging.info(f"Starting DNS logger process; monitoring folder: {self.dnsLogDir} every {interval} seconds.")
        else:
            logging.info(f"Running DNS logger once on folder: {self.dnsLogDir}")

        while True:
            for file in [f for f in listdir(self.dnsLogDir) if f.endswith(".log")]:
                logging.debug(f"Parsing log file: {file}")
                self._read_log(self.dnsLogDir + "/" + file)
            if interval:
                time.sleep(interval)
            else:
                return


    def _read_log(self, file) -> None:
        # bash filters by outgoing traffic, and removes router traffic, then clears log file
        bash = f'cat {file} | grep -Fvw $(hostname -i) | grep -F "from" | cut -d\  -f1,2,3,6,8 && > {file}'
        output = self.shell.execute(bash)
        for line in filter(None, output): # ignore empty lines
            self._process_line(line)


    def _process_line(self, line :str) -> None:
        line = line.split(" ")
        timr_str = line[0:3]
        dest = line[3]
        for ignore in IGNORE:
            if ignore in dest:
                return
        try:
            ip = IpAddress(line[4])
        except InvalidIpv4Exception:
            return
        time = self._get_time(timr_str)
        self._add_to_database(time, dest, ip)


    def _get_time(self, inputString : str) -> int:
        time = [str(datetime.today().year)] + inputString
        dateTime = datetime.strptime("-".join(time), "%Y-%b-%d-%H:%M:%S")
        # if calculated date is in the future, it must have rolled over 
        # from december to january, so subtract 1 year.
        if dateTime > datetime.now():
            dateTime -= datetime.timedelta(years=1)
        return dateTime


    def _add_to_database(self, time : datetime, destination : str, ip : IpAddress) -> None:
        mac = self._get_mac_from_ip(ip)
        if not mac:
            return
        # insert into queried table
        sqlString = """ INSERT INTO
                            queried (mac, destination, time)
                        VALUES (:mac, :dest, :time); """
        with self.db as cur:
            cur.execute(sqlString, {"mac":mac, "dest":destination, "time":time})
            logging.debug(f"Saving query event at {time} for device {mac} to {destination}.")

            if self._default_blocking_enabled(mac, cur):
                cur.execute("""INSERT OR IGNORE INTO block_allow VALUES(?, ?, ?) ;""", (mac, destination, 1))
                logging.info(f"Destination: {destination} blocked for device: {mac} as default trimming is enabled.")
            
            if self._location_identified(destination, cur):
                logging.info(f"Destination {destination} already identiified and saved in database")
                return
            self.locator.locate_and_save(destination, cur)
    

    def _location_identified(self, destination : str, cur : sqlite3.Cursor):
        cur.execute("SELECT location_identified FROM destination WHERE name = (?) ;", (destination, ))
        result = cur.fetchone()
        if not result:
            return
        return bool(result[0])


    def _default_blocking_enabled(self, mac : MacAddress, cur : sqlite3.Cursor):
        cur.execute("SELECT block_default FROM device WHERE mac = (?) ;", (mac, ))
        result = cur.fetchone()
        if not result:
            return
        return bool(result[0])

    def _get_mac_from_ip(self, ip : IpAddress) -> MacAddress:
        sqlString = """ SELECT mac FROM device WHERE ip = (?) ; """
        with self.db as cur:
            cur.execute(sqlString, (ip, ))
            try:
                mac = cur.fetchone()[0]
                return MacAddress(mac)
            except TypeError:
                logging.error(f"Device not found in database. Device has IP: {ip}")
                return None


def main():
    logging.basicConfig(filename='/opt/iotrimmer/logs/dnsLogger.log',
                        filemode='a',
                        format='%(asctime)s - %(name)s %(levelname)s %(message)s',
                        datefmt='%H:%M:%S',
                        level=logging.INFO)

    DnsLogger(Database(), Locator()).start(interval=TIME_INTERVAL)


if __name__ == "__main__":
    main()

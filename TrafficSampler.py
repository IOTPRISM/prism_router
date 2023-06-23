from TrafficSniffer import TrafficSniffer
from MacAddress import MacAddress
from Database import Database
from subprocess import Popen
from time import sleep
from Shell import Shell
import logging


class TrafficSampler:

    def __init__(self, shell = None, database = None) -> None:
        self.shell = Shell() if not shell else shell
        self.database = Database() if not database else database
        self.interval = self.get_interval()
        self.window = self.get_window_size()
        self.macs = self.get_macs()
        self.pid = self.get_pid()


    def get_macs(self) -> None:
        with self.database as cur:
            sqlString = " SELECT mac FROM device WHERE sniff = 1;"
            cur.execute(sqlString)
            return [MacAddress(x[0]) for x in cur.fetchall()]
    

    def get_pid(self) -> None:
        try:
            self.pid = self.shell.execute(f"/opt/bin/pgrep -f 'TrafficSampler.py'")[0]
        except IndexError:
            self.pid = None
        

    def begin(self) -> None:
        if self.pid:
            logging.error("Traffic sampler already runnung, can't be run again")
            return
        process = Popen(['/opt/bin/python3', '/opt/iotrimmer/TrafficSampler.py'])
        self.pid = process.pid


    def stop(self) -> None:
        if self.pid:
            self.shell.execute(f"/bin/kill {self.pid}")
        else:
            logging.error("Traffic sampler not running, cannot be stopped.")
            

    def restart(self) -> None:
        self.stop()
        self.__init__()
        self.begin()


    def sniff_all(self) -> None:
        for mac in self.macs:
            data = TrafficSniffer(mac).sniff_by_mac(self.window)    
            if not data:
                continue
            keys = data.keys()
            sqlString = f"""INSERT INTO
                                traffic_capture (mac, {', '.join([k for k in keys])})
                            VALUES
                                (:{mac}, {', '.join([f":{k}" for k in keys])}); """
            with self.database as cur:
                cur.execute(sqlString, data)
    
    
    def set_interval(self, interval : int) -> None:
        with self.database as cur:
            cur.execute("UPDATE traffic_sniffer SET interval = (?);", (interval,))


    def get_interval(self) -> int:
        with self.database as cur:
            cur.execute("SELECT interval from traffic_sniffer;")
            return int(cur.fetchone()[0])

    
    def set_window_size(self, window : int) -> int:
        with self.database as cur:
            cur.execute("UPDATE traffic_sniffer SET window = (?);", (window,))
    

    def get_window_size(self) -> int:
        with self.database as cur:
            cur.execute("SELECT window from traffic_sniffer;")
            return int(cur.fetchone()[0])


if __name__ == "__main__":
    trafficSampler = TrafficSampler()
    while True:
        trafficSampler.sniff_all()
        sleep(trafficSampler.interval)

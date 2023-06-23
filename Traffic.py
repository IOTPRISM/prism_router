from Clock import Clock
from Devices import Devices
import json, sqlite3


class Traffic:


    def __init__(self, cur : sqlite3.Cursor, clock = None) -> None:
        self.cur = cur
        self.clock = Clock() if not clock else clock
        self.blockedByType = {}
        self.allowed = {}
        self._load_last_day_allowed_traffic()
        for typ in ["first", "support", "third"]:
            self._load_last_day_blocked_traffic_by_type(typ)


    def load_last_day_device_traffic(self, devices : Devices):
        self._load_last_day_device_queried_traffic(devices)
        self._load_last_day_device_blocked_traffic(devices)


    def _load_last_day_blocked_traffic_by_type(self, type) -> None:
        yesterday = self.clock.yesterday()
        sqlString = """SELECT
                            substr(time,12,4) AS mins,
                            count(time) AS count,
                            destination.party
                        FROM
                            queried
                        INNER JOIN
                            block_allow ON block_allow.destination = queried.destination
                        INNER JOIN
                            destination ON destination.name = queried.destination
                        AND
                            block_allow.mac = queried.mac
                        WHERE
                            queried.time > :yesterday
                        AND 
                            destination.party = :party
                        GROUP BY
                            mins;"""
        data =  {"yesterday": yesterday, "party":type}
        self.cur.execute(sqlString, data)
        traffic = {}
        for q in self.cur.fetchall():
            traffic[q['mins'] + '0'] = q['count']
        self.blockedByType[type] = traffic


    def _load_last_day_allowed_traffic(self) -> None:
        yesterday = self.clock.yesterday()
        sqlString = """SELECT
                            destination AS dest,
                            substr(time,12,4) AS mins,
                            count(time) AS count
                        FROM
                            queried
                        WHERE
                            NOT EXISTS (SELECT
                                            destination
                                        FROM
                                            block_allow
                                        WHERE
                                            dest = destination
                                        AND
                                            queried.mac = block_allow.mac
                                        AND
                                            block_allow.block = 1)
                        AND
                            time > :yesterday
                        GROUP BY
                            mins; """
        self.cur.execute(sqlString, {"yesterday": yesterday})
        traffic = {}
        for q in self.cur.fetchall():
            traffic[q['mins'] + '0'] = q['count']
        self.allowed = traffic


    def _load_last_day_device_queried_traffic(self, devices : Devices) -> None:
        yesterday = self.clock.yesterday()
        self.deviceTraffic = {}
        for d in devices:
            traffic = {}
            sqlString = """SELECT
                                substr(time,12,4) AS mins,
                                count(time) AS count
                            FROM
                                queried
                            WHERE
                                time > :yesterday 
                            AND
                                mac = :mac
                            GROUP BY
                                mins; """
            self.cur.execute(sqlString, {"yesterday": yesterday, "mac": d.mac})
            for q in self.cur.fetchall():
                traffic[q['mins'] + '0'] = q['count']
            self.deviceTraffic[d.mac] = traffic


    def _load_last_day_device_blocked_traffic(self, devices : Devices) -> None:
        yesterday = self.clock.yesterday()
        self.deviceBlockedTraffic = {}
        for d in devices:
            blockedTraffic = {}
            sqlString = """ SELECT
                                substr(time,12,4) AS mins,
                                count(time) AS count,
                                destination.party
                            FROM
                                queried
                            INNER JOIN
                                block_allow ON block_allow.destination = queried.destination
                            AND
                                block_allow.mac = queried.mac
                            INNER JOIN
                                destination ON destination.name = queried.destination
                            WHERE
                                time > :yesterday 
                            AND
                                block_allow.mac = :mac
                            AND
                                block_allow.block = 1
                            GROUP BY
                                mins;"""
            data = {"yesterday": yesterday, "mac": d.mac}
            self.cur.execute(sqlString, data)
            for q in self.cur.fetchall():
                blockedTraffic[q['mins'] + '0'] = q['count']
            self.deviceBlockedTraffic[d.mac] = blockedTraffic


    def json_last_day_device_traffic(self, mac, blocked = False):
        t = self.deviceTraffic[mac] if blocked == False else self.deviceBlockedTraffic[mac]
        return json.dumps(t)


    def get_last_day_blocked_by_type(self, typ):
        return self.blockedByType[typ]


class TrafficMetrics:


    def __init__(self, cur : sqlite3.Cursor) -> None:
        self.cur = cur
        self.load_total_queried()
        self.load_total_blocked()
        self.load_percentage_blocked()
        self.load_third_support_percentage_blocked()
    

    def load_total_queried(self) -> None:
        self.cur.execute("SELECT count(*) FROM queried;")
        self.totalQueried = self.cur.fetchone()[0]
       

    def load_total_blocked(self) -> None:
        sqlString = """ SELECT
                            count(block_allow.destination)
                        FROM
                            queried
                        INNER JOIN 
                            block_allow ON queried.destination = block_allow.destination
                        AND
                            block_allow.mac = queried.mac
                        AND
                            block_allow.block = 1 ; """
        self.cur.execute(sqlString)
        self.totalBlocked = self.cur.fetchone()[0]


    def load_percentage_blocked(self) -> None:
        self.cur.execute(" SELECT count(*) AS c FROM queried; ")
        if totalQueried := self.cur.fetchone()[0]:
            self.percentageBlocked = round((self.totalBlocked / totalQueried) * 100, 1)
        else:
            self.percentageBlocked = 0


    def load_third_support_percentage_blocked(self) -> None:
        sqlString = """ SELECT
                            count(party) AS c
                        FROM
                            destination
                        INNER JOIN
                            queried ON queried.destination = destination.name
                        INNER JOIN 
                            block_allow ON queried.destination = block_allow.destination
                        AND
                            block_allow.mac = queried.mac
                        WHERE
                            party IN ('third', 'support'); """
        self.cur.execute(sqlString)
        thirdSupportBlocked = self.cur.fetchone()[0]
        rounded = round(thirdSupportBlocked / self.totalBlocked * 100, 1) if self.totalBlocked else 0
        self.thirdSupportPercentageBlocked = rounded

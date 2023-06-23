import sqlite3, json, urllib.request, logging
from Database import Database

API_URL = 'http://192.168.2.104/'


class BlocklistFetch:


    def __init__(self, cur : sqlite3.Cursor):
        self.cur = cur
        self.cur.execute("SELECT version FROM blocklist_version;") 
        currentVersion = int(self.cur.fetchone()[0])

        with urllib.request.urlopen(API_URL + 'getVersion') as url:
            self.remoteVersion = json.loads(url.read().decode())

        self.upToDate = True if currentVersion == self.remoteVersion else False
        logging.info(f"Local blocklist version = {currentVersion}. Remote blocklist version = {self.remoteVersion}")

        if not self.upToDate:
            with urllib.request.urlopen(API_URL + 'fetchBlocklist') as url:
                self.data = json.loads(url.read().decode())


    def save(self):
        if self.upToDate:
            return
        self.cur.execute(" DELETE FROM blocklist; ")
        for product, domains in self.data.items():
            self.cur.execute(""" INSERT OR IGNORE INTO
                                product (name)
                            VALUES (?); """, (product, ))
            for domain, party in domains:
                self.cur.execute(""" INSERT OR IGNORE INTO
                                    blocklist (product, destination)
                                VALUES (?,?);  """, (product, domain))
                self.cur.execute(""" INSERT OR IGNORE INTO
                                    destination (name, party)
                                VALUES (?,?); """, (domain, party))
        self.cur.execute("UPDATE blocklist_version SET version = (?)", (self.remoteVersion, ))


if __name__ == "__main__":
    with Database() as cur:
        BlocklistFetch(cur).save()

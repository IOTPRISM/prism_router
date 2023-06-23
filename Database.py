import sqlite3, errno, os, logging
from Shell import Shell
from DictObj import DictObj
from datetime import datetime

SCHEMA = """CREATE TABLE device (
                mac INTEGER NOT NULL PRIMARY KEY,
                name TEXT NOT NULL,
                ip INTEGER NOT NULL,
                hostname TEXT,
                product TEXT REFERENCES product(name) DEFAULT NULL,
                mac_vendor TEXT DEFAULT NULL,
                user_identified BOOLEAN DEFAULT 0,
                auto_identified BOOLEAN DEFAULT 0,
                custom_icon BOOLEAN DEFAULT 0,
                activated BOOLEAN DEFAULT 1,
                block_default BOOLEAN DEFAULT 0,
                icon TEXT DEFAULT NULL,
                deleted BOOLEAN DEFAULT 0,
                sniff BOOLEAN DEFAULT 1,
                UNIQUE (mac),
                UNIQUE (ip));

            CREATE TABLE product (
                name TEXT NOT NULL PRIMARY KEY,
                vendor TEXT);

            CREATE TABLE destination (
                name TEXT NOT NULL PRIMARY KEY,
                iso_code TEXT DEFAULT NULL,
                latitude DOUBLE DEFAULT NULL,
                longitude DOUBLE DEFAULT NULL,
                location_identified BOOLEAN DEFAULT NULL,
                party TEXT);

            CREATE TABLE blocklist (
                product TEXT NOT NULL REFERENCES product(name),
                destination TEXT NOT NULL REFERENCES destination(name),
                UNIQUE (product, destination));

            CREATE TABLE queried (
                mac INTEGER NOT NULL REFERENCES device(mac) ON DELETE CASCADE,
                destination TEXT NOT NULL REFERENCES destination(name) ON DELETE CASCADE,
                time INTEGER NOT NULL);

            CREATE INDEX queried_index ON queried(mac, destination, time);

            CREATE TABLE block_allow (
                mac INTEGER NOT NULL REFERENCES device(mac) ON DELETE CASCADE,
                destination TEXT NOT NULL REFERENCES destination(name) ON DELETE CASCADE,
                block BOOLEAN DEFAULT 0, 
                UNIQUE (mac, destination));

            CREATE TABLE blocklist_version (
                version INTEGER NOT NULL PRIMARY KEY);

            CREATE TABLE fcm_token (
                token TEXT NOT NULL,
                UNIQUE (token));

            CREATE TABLE traffic_sniffer (
                interval INTEGER NOT NULL,
                window INTEGER NOT NULL);

            CREATE TABLE traffic_capture (
                mac INTEGER NOT NULL REFERENCES device(mac),
                time INTEGER NOT NULL,
                length INTEGER,
                UDP INTEGER,
                TCP INTEGER,
                HTTP INTEGER,
                HTTPS INTEGER);

            INSERT INTO blocklist_version VALUES (0);
            INSERT INTO traffic_sniffer VALUES (6000, 30); """


class Database:


    def __init__(self, dbFile='/opt/iotrimmer/iotrimmer.db', dictCursor = True) -> None:
        self.dbFile = dbFile
        self.dictCursor = dictCursor
    

    @staticmethod
    def convert_time_string(time : str) -> datetime:
        return datetime.strptime(time, '%Y-%m-%d %H:%M:%S')


    def __enter__(self) -> sqlite3.Cursor:
        if not os.path.isfile(self.dbFile):
            raise FileNotFoundError(
                errno.ENOENT, os.strerror(errno.ENOENT), self.dbFile)
        self.conn = sqlite3.connect(self.dbFile)
        self.conn.row_factory = sqlite3.Row if self.dictCursor else None
        self.cur = self.conn.cursor()
        return self.cur
    

    def __exit__(self, exc_type, exc_val, exc_tb) -> None:
        self.cur.close()
        self.conn.commit()


    def create_database(self, schema = SCHEMA) -> None:
        if os.path.isfile(self.dbFile):
            raise FileExistsError(
                errno.ENOENT, os.strerror(errno.ENOENT), self.dbFile)
        open(self.dbFile, 'w').close() # create file
        with self as cur:
            cur.executescript(schema)
        logging.info(f"Database created in {self.dbFile}.")
                

    def clear_database(self) -> None:
        sqlString = """ SELECT
                            name
                        FROM
                            sqlite_master
                        WHERE
                            type='table';"""
        with self as cur:
            tables = cur.execute(sqlString)
            cmds = " ".join([f"DELETE FROM {t[0]};" for t in tables])
            cur.executescript(cmds)
            cur.execute("INSERT INTO blocklist_version VALUES (0);")
        logging.warning(f"Database cleared at {self.dbFile}.")


    def version(self) -> int:
        sqlString = """ SELECT
                            version
                        FROM
                            blocklist_version
                        LIMIT
                            1; """
        with self as cur:
            cur.execute(sqlString)
            return cur.fetchone()[0]


    def size(self, shell : Shell) -> str:
        # returns size of DB on disk in KB
        out = shell.execute(f"du -h {self.dbFile} | cut -f1")[-1]
        return f'{out[:-1]} {out[-1]}B'


    def metrics(self, shell = None) -> dict:
        shell = shell if shell else Shell()
        metrics = DictObj()
        sqlString = """ SELECT
                            count(destination),
                            count(DISTINCT destination)
                        FROM
                            queried; """
        with self as cur:
            cur.execute(sqlString)
            metrics["totalDestCount"], metrics["uniqueDestCount"] = cur.fetchone()

        sqlString = """ SELECT
                            count(destination) AS count
                        FROM
                            block_allow
                        WHERE   
                            block = 1; """
        with self as cur:
            cur.execute(sqlString)
            metrics["blockedCount"] = cur.fetchone()[0]

        metrics["size"] = self.size(shell)
        
        with self as cur:
            cur.execute("SELECT version FROM blocklist_version;")
            metrics["blocklistVersion"] = cur.fetchone()[0]

        return metrics



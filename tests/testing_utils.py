
import sys, os, random, string
from datetime import datetime
sys.path.append('../')
from Database import Database
from Device import Device
from Locator import Location
from IpAddress import IpAddress
from MacAddress import MacAddress

DB_TEST_FILE = 'iotrimmer.db.test'

def safe_remove(f):
    try:
        os.remove(f)
    except OSError:
        pass


def initialise_test_database(file :str) -> Database:
    os.remove(file)
    db = Database(dbFile=file)
    db.create_database()
    return db


def default_device() -> Device:
    return Device({"product": "exampleProduct",
                    "user_identified": False,
                    "auto_identified": False,
                    "vendor": "exampleVendor",
                    "name": None,
                    "mac": "exampleMac",
                    "ip": "192.168.43." + str(random.randint(1, 254)),
                    "hostname": ''.join(random.choice(string.ascii_lowercase) for _ in range(20)),
                    "custom_icon": False})


def random_location() -> Location:
    return Location({   "latitude": random.randint(-90, 90),
                        "longitude": random.randint(-180, 180),
                        "count": random.randint(0, 10),
                        "iso_code": random.choice(["US", "UK", "IE", "FR"]),
                        "normalised": False})


def default_location() -> Location:
    return Location({   "latitude": 90,
                        "longitude": 180,
                        "count": 1,})

def random_mac():
    return MacAddress("02:00:00:%02x:%02x:%02x" % ( random.randint(0, 255),
                                                    random.randint(0, 255),
                                                    random.randint(0, 255)))


def random_string(size):
    return ''.join(random.choice(string.ascii_lowercase) for _ in range(size))


def random_nums(size):
    return ''.join(random.choice(string.digits) for _ in range(size))


def sequential_ip():
    num = 1
    while num < 255:
        yield IpAddress(f"192.168.1.{num}")
        num += 1

def populate_test_database(file :str) -> None:
    with initialise_test_database(file) as cur:
        ip_generator = sequential_ip()
        for _ in range(50):
            randUrlAllow = random_string(10) + 'allow.com'
            randUrlBlock = random_string(10) + 'block.com'
            randVendor = random_string(10) + " Inc."
            randMac = random_mac()
            randProduct = random_string(15)
            randLoc = random_location()
            randParty = random.choice(["first", "third", "support"])

            # add devices
            cur.execute(f""" INSERT OR IGNORE INTO
                                device (mac, ip, hostname, product)
                            VALUES
                                (?, ?, ?, ?) """, (randMac, next(ip_generator), random_string(10), randProduct))
            
            cur.execute(f""" INSERT OR IGNORE INTO
                                product (name, vendor)
                            VALUES
                                (?, ?)""", (randProduct, randVendor))


            # add queries to destination
            cur.execute(f""" INSERT OR IGNORE INTO
                                destination (name, iso_code, latitude, longitude, party)
                            VALUES
                                (?, ?, ?, ?, ?)""", (randUrlAllow, randLoc.iso_code, randLoc.latitude, randLoc.longitude, randParty))
            
            cur.execute(f""" INSERT OR IGNORE INTO
                                destination (name, iso_code, latitude, longitude, party)
                            VALUES
                                (?, ?, ?, ?, ?)""", (randUrlBlock, randLoc.iso_code, randLoc.latitude, randLoc.longitude, randParty))

            
            
            # add block_allow queries
            cur.execute(f""" INSERT OR IGNORE INTO
                                block_allow (mac, destination, block)
                            VALUES
                                (?, ?, 0)""", (randMac, randUrlBlock))
            
            cur.execute(f""" INSERT OR IGNORE INTO
                                block_allow (mac, destination, block)
                            VALUES
                                (?, ?, 1)""", (randMac, randUrlAllow))


            # add urls to queried
            cur.execute(f""" INSERT OR IGNORE INTO
                                queried (mac, destination, time)
                            VALUES
                                (?, ?, ?)""", (randMac, randUrlBlock, datetime.now()))

            
            cur.execute(f""" INSERT OR IGNORE INTO
                                queried (mac, destination, time)
                            VALUES
                                (?, ?, ?)""", (randMac, randUrlAllow, datetime.now()))


def add_device_to_database(dbFile :str, ip :IpAddress, mac :MacAddress, hostname :str) -> None:
    with Database(dbFile) as cur:
        Device({"mac": mac,
                "ip": ip,
                "hostname": hostname}).update_database(cur)


def populate_dns_log_file(fileName :str, query :str, ip :IpAddress) -> None:
    with open(fileName, 'w') as f:
        f.write(f'Oct  8 16:50:27 dnsmasq[2258]: query[A] {query} from {ip.__str__()}\n') 
        f.write(f'Oct  8 16:50:30 dnsmasq[2258]: query[A] {query} from {ip.__str__()}\n') 
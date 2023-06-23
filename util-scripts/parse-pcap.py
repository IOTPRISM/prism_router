import sqlite3, sys
from datetime import datetime
from scapy.all import rdpcap, Ether, DNSQR, IP
sys.path.append('../')
from Database import Database


def main():
    mac = sys.argv[1]
    pathToPcap = sys.argv[2]
    pcap = rdpcap(pathToPcap)

    entries = []
    for pkt in pcap:
        try:
            if pkt.haslayer(DNSQR) and pkt[Ether].src == mac:
                dest = pkt[DNSQR].qname.decode()[:-1]
                time = datetime.fromtimestamp(pkt.time)
                entries.append((mac, dest, time))
        except IndexError:
            pass

    with Database(dbFile='../iotrimmer.db') as cur:
        cur.executemany("INSERT INTO queried VALUES (?, ?, ?)", entries)


if __name__ == "__main__":
    main()
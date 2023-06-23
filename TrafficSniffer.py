from scapy import packet
from datetime import datetime
from statistics import mean
from collections import Counter
from MacAddress import MacAddress
from Network import Network
from scapy.all import sniff, IP, TCP, UDP


class TrafficSniffer:


    def __init__(self, mac : MacAddress) -> None:
        self.mac = mac
        self.data = []


    def sniff_by_mac(self, window : int) -> None:
        ifaces = [i for i, _ in Network().wifiInterfaces]

        def packet_callback(pkt) -> dict:
            if IP not in pkt:
                return
            protocol = "TCP" if TCP in pkt else None
            protocol = "UDP" if UDP in pkt else None
            dport = "http" if protocol == "TCP" and pkt[TCP].dport == 80 else None
            dport = "http" if protocol == "TCP" and pkt[TCP].dport == 443 else None
            data = (pkt.sprintf("%IP.len%"), protocol, dport)
            self.data.append(data)

        data = {}
        data["time"] = datetime.now()

        sniff(iface = ifaces, prn = packet_callback,
                lfilter = lambda d : d.src == str(self.mac), timeout = window)

        if not self.data:
            return None

        data["length"] = mean([int(l) for l, _, _ in self.data])
        data.update(Counter(filter(None, [p for _, p, _ in self.data])))
        data.update(Counter(filter(None, [p for _, _, p in self.data])))
        return data


if __name__ == "__main__":
    TrafficSniffer(MacAddress(36145254884654)).sniff_by_mac()

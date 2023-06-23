import logging, sqlite3, time
from Shell import Shell
from Database import Database
from pathlib import Path
from MacAddress import MacAddress


class DnsConfFile:
    

    def __init__(self, mac : MacAddress, dir = "/opt/iotrimmer/dns-override/") -> None:
        self.mac = mac
        self.dir = dir
        self.confFile = Path(self.dir + str(self.mac) + "_dnsmasq.conf")
        self.domains = set()
        self._get_port_and_address()
        if  self.confFile.is_file():
            self._load_domains()
        else:
            self._create_new_file()
            logging.info(f"Created new DNS conf file for device with Mac address: {self.mac} in {self.confFile}.")


    def _get_port_and_address(self) -> None:
        # compute a unique ip, port pair based off a device's mac address
        octets = self.mac.__str__().split(':')
        base10 = list(map(lambda x : str(int(x, 16)), octets))
        self.listenAddr = "127.53." + base10[2] + '.' + base10[3]
        self.port = 48620 + int(base10[4]) + int(base10[5])
        
        
    def _create_new_file(self) -> None:
        with open(self.confFile, 'w') as conf:
            conf.write("bind-interfaces\n")
            conf.write(f"listen-address={self.listenAddr}\n")
            conf.write(f"port={self.port}\n")
            conf.write(f"resolv-file=/tmp/resolv.dnsmasq\n")
            conf.write(f"cache-size=0\n")
            conf.write(f"log-queries\n")
            conf.write(f"log-facility=/opt/iotrimmer/dns-override/{self.mac}_dnsmasq.log\n")


    def _load_domains(self) -> None:
        with open(self.confFile, 'r') as conf:
            lines = conf.readlines()
        domainLines = filter(lambda x : x.startswith("address=/"), lines)
        domains = map(lambda x : x[9:-2], domainLines)
        self.domains.update(domains)


    def save_domains(self) -> None:
        self._create_new_file()
        with open(self.confFile, 'a+') as conf:
            for d in self.domains:
                conf.write(f"address=/{d}/\n")
        logging.info(f"Updating blocked domains in DNS override file: {self.confFile} for device with Mac Address: {self.mac}.")


    def add_domain(self, domain) -> None:
        if domain in self.domains:
            return
        self.domains.add(domain)
        logging.info(f"Adding blocked domain {domain} for device with Mac address: {self.mac}.")

    
    def remove_domain(self, domain) -> None:
        self.domains.remove(domain)
        logging.info(f"Removing blocked domain {domain} for device with Mac address: {self.mac}.")


    def clear_domains(self) -> None:
        self.domains = set()


class DnsOverride:


    def __init__(self, cur : sqlite3.Cursor, shell = None):
        self.shell = shell if shell else Shell()
        self.cur = cur
        self.dnsConfFiles = {}
        self.dnsMasqProcs = {}
        self.iptablesStatus = {}
        sqlString = """ SELECT
                            mac
                        FROM
                            device
                        WHERE
                            deleted = 0
                        AND
                            activated = 1; """
        self.cur.execute(sqlString)

        for dev in self.cur.fetchall():
            mac = MacAddress(dev["mac"])
            file = DnsConfFile(mac)
            self.dnsConfFiles[mac] = file
            try:
                self.dnsMasqProcs[mac] = self.shell.execute(f"/opt/bin/pgrep -f {file.confFile}")[0]
            except IndexError:
                continue
            self.iptablesStatus[mac] = bool(len(self.shell.execute(f"/usr/sbin/iptables -t nat -S | grep {str(mac).upper()}")))
    

    def start_dns_masq(self, mac : MacAddress) -> None:
        if mac in self.dnsMasqProcs:
            return
        self.dnsConfFiles[mac] = DnsConfFile(mac)
        file = self.dnsConfFiles[mac]
        self.shell.execute(f"/usr/sbin/dnsmasq -u root -g root -C {file.confFile}")
        pid = self.shell.execute(f"/opt/bin/pgrep -f {file.confFile}")[0]
        logging.info(f"Starting DNSmasq process for device: {file.mac}, with conf file: {file.confFile} and PID: {pid}")
        self.dnsMasqProcs[file.mac] = pid


    def stop_dns_masq(self, mac : MacAddress) -> None:
        if mac not in self.dnsMasqProcs:
            return
        pid = self.dnsMasqProcs[mac]
        self.shell.execute(f"/bin/kill {pid}")
        del self.dnsMasqProcs[mac]
        logging.info(f"Stopping DNSmasq process for device: {mac}, with PID: {pid}")


    def iptables_up(self, mac : MacAddress) -> None:
        if mac in self.iptablesStatus and self.iptablesStatus[mac]:
            return
        file = self.dnsConfFiles[mac]
        self.shell.execute(f"/usr/sbin/iptables -t nat -A PREROUTING -i br0 -m mac --mac-source {mac} -p udp -m udp --dport 53 -j DNAT --to {file.listenAddr}:{file.port}")
        self.shell.execute(f"/usr/sbin/iptables -t nat -A PREROUTING -i br0 -m mac --mac-source {mac} -p tcp --dport 53 -j DNAT --to {file.listenAddr}:{file.port}")
        logging.info(f"Setting iptables rules for redirecting DNS traffic of device: {mac} to {file.listenAddr}:{file.port}")
        self.iptablesStatus[mac] = True


    def iptables_down(self, mac : MacAddress) -> None:
        file = self.dnsConfFiles[mac]
        self.shell.execute(f"/usr/sbin/iptables -t nat -D PREROUTING -i br0 -m mac --mac-source {mac} -p udp -m udp --dport 53 -j DNAT --to {file.listenAddr}:{file.port}")
        self.shell.execute(f"/usr/sbin/iptables -t nat -D PREROUTING -i br0 -m mac --mac-source {mac} -p tcp --dport 53 -j DNAT --to {file.listenAddr}:{file.port}")
        logging.info(f"Removing iptables rules for redirecting DNS traffic of device: {mac} to {file.listenAddr}:{file.port}")
        self.iptablesStatus[mac] = False


    def begin(self) -> None:
        for file in self.dnsConfFiles.values():
            self.sync(file.mac)
            self.iptables_up(file.mac)


    def add(self, mac : MacAddress, domains : list) -> None:
        file = self.dnsConfFiles[mac]
        for domain in domains:
            file.add_domain(domain)
        file.save_domains()


    def remove(self, mac : MacAddress, domains : list) -> None:
        file = self.dnsConfFiles[mac]
        for domain in domains:
            file.remove_domain(domain)
        file.save_domains()


    def sync(self, mac : MacAddress) -> None:
        self.stop_dns_masq(mac)
        file = DnsConfFile(mac)
        file.clear_domains()
        sqlString = """ SELECT
                                destination
                            FROM 
                                block_allow
                            WHERE
                                mac = :mac
                            AND
                                block = 1; """
        self.cur.execute(sqlString, {"mac" : mac})
        for blocked in self.cur.fetchall():
            file.add_domain(blocked["destination"])
        file.save_domains()
        self.start_dns_masq(mac)
            

    def deactivate(self, mac : MacAddress) -> None:
        self.stop_dns_masq(mac)
        self.iptables_down(mac)


    def activate(self, mac : MacAddress) -> None:
        self.start_dns_masq(mac)
        self.iptables_up(mac)


def main():

    logging.basicConfig(filename = '/opt/iotrimmer/logs/dnsOverride.log',
                        filemode = 'a',
                        format = '%(asctime)s - %(name)s %(levelname)s %(message)s',
                        datefmt = '%H:%M:%S',
                        level = logging.DEBUG)

    with Database() as cur:
        DnsOverride(cur).begin()

if __name__ == "__main__":
    main()

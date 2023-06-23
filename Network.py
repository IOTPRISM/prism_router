from utils import is_valid_passphrase, is_valid_ssid, get_macs_from_str
from Shell import Shell
from IpAddress import IpAddress, InvalidIpv4Exception
from MacAddress import MacAddress
import logging


class Network:
    
    
    def __init__(self, shell = None) -> None:
        self.shell = Shell() if not shell else shell
        self.nameServers = []
        self.wifiInterfaces = set()
        self._load_info()
        self._load_wifi_interfaces()
        self._load_wifi_credentials()


    def _load_info(self) -> None:
        output = self.shell.execute("nvram get wan_dns")[0]
        nameServers = output.split("=")[-1]
        for ns in nameServers.split(" "):
            self.nameServers.append(IpAddress(ns))
        self.hostname  = self.shell.execute("hostname")[0].strip()
        self.ip = self.shell.execute("hostname -i")[0]
        self.wanInterface = self.shell.execute("ip -o -4 route show to default | cut -d ' ' -f5")[0]
        macShellOutput = self.shell.execute(f"ip link show {self.wanInterface} | tail -1")[0]
        self.wanInterfaceMac = get_macs_from_str(macShellOutput)[0]
        ip = self.shell.execute(f"ip -f inet addr show {self.wanInterface} | awk '/inet/ {{print $2}}' | cut -d/  -f1")[0]
        self.wanIp = IpAddress(ip)
                

    def _load_wifi_interfaces(self) -> None:
        bash = "ps w | grep 'hostapd' | sed 's/|/ /' | awk '{print $9}' | grep -v 'grep'"
        output = self.shell.execute(bash)
        if not output:
            logging.error("No hostapd processes found.")
            return
        for line in output:
            start = max([i for i, ch in enumerate(line) if ch == '/']) # find largest index of / character
            end = line.find('_')
            interface = line[start+1:end]
            macShellOutput = self.shell.execute(f"ip link show {interface} | tail -1")[0]
            mac = get_macs_from_str(macShellOutput)[0]
            self.wifiInterfaces.add((interface, mac))
            logging.debug(f"Interface running access point found: {interface}")


    def _load_wifi_credentials(self) -> None:
        # assume passphrase and ssid are the same for all interfaces,
        # we just read the first one
        interface = next(iter(self.wifiInterfaces))
        self.ssid = self.shell.execute(f"nvram get {interface[0]}_ssid")[0]
        self.passphrase = self.shell.execute(f"nvram get {interface[0]}_wpa_psk")[0]


    def set_wifi_passphrase(self, passphrase : str) -> None:
        if self.passphrase == passphrase:
            return
        if not is_valid_passphrase(passphrase):
            logging.error("Invalid password setting attempted")
            return
        for interface, mac in self.wifiInterfaces:
            self.shell.execute(f"nvram set {interface}_wpa_psk={passphrase}")
            logging.info(f"Wifi passphrase set on {interface} with {mac}.")


    def set_wifi_ssid(self, ssid : str) -> None:
        if self.ssid == ssid:
            return
        if not is_valid_ssid(ssid):
            logging.error(f"Invalid ssid setting attempted: {ssid}")
            return
        for interface, mac in self.wifiInterfaces:
            self.shell.execute(f"nvram set {interface}_ssid={ssid}")
            logging.info(f"Wifi SSID set on {interface} with {mac} to {ssid}.")


    def set_name_servers(self, nameServerStr : list) -> None:
        newNameServers = nameServerStr.split(",")
        newNameServers = filter(None, [ns.strip() for ns in newNameServers])
        try:
            newNameServerIps = list(map(IpAddress, newNameServers))
        except InvalidIpv4Exception:
            logging.error(f"Invalid name servers adding attempted: {newNameServers}")
            return
        if self.nameServers == newNameServerIps:
            return
        self.nameServers = newNameServerIps
        nameServers = " ".join(map(str, self.nameServers))
        self.shell.execute(f"nvram set wan_dns='{nameServers}'")
        logging.info(f"Saving updated name servers: {nameServers}")


    def save_changes(self) -> None:
        self.shell.execute("nvram commit")
        
    
    def print_name_servers(self) -> str:
        return ", ".join(map(str, self.nameServers))


    def print_wifi_interface(self) -> str:
        return ", ".join(map(lambda x : x[0], self.wifiInterfaces))


    def print_wifi_interface_mac(self) -> str:
        return ", ".join(set(map(lambda x : str(x[1]), self.wifiInterfaces)))

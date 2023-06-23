import sqlite3, re, ipaddress, struct


class InvalidIpv4Exception(Exception):


    def __init__(self, ip):
        super().__init__(f"{ip} is not a valid IPV4 address.")


class IpAddress:


    def __init__(self, ip):
        if isinstance(ip, float) or isinstance(ip, int):
            if not self.check_int(ip):
                raise InvalidIpv4Exception(ip)
            self.int = ip
            self.str = str(ipaddress.IPv4Address(ip))

        elif isinstance(ip, str):
            ip = ip.lower()
            if not self.check_str(ip):
                raise InvalidIpv4Exception(ip)
            self.int = int(ipaddress.IPv4Address(ip.strip()))
            self.str = ip

        elif isinstance(ip, IpAddress):
            self = ip
        else:
            raise InvalidIpv4Exception(ip)


    def __eq__(self, other):
        return self.str == other.str


    def __hash__(self):
        return hash(self.str)


    @staticmethod
    def int(ipAddress) -> int:
        return ipAddress.to_int()
    

    def to_int(self) -> int:
        return self.int


    def __str__(self) -> str:
        return self.str


    def check_int(self, ipInt) -> bool:
        return False if ipInt > 2**32 -1 or ipInt < 0 else True


    def check_str(self, ipStr) -> bool:
        regexPattern = "^([0-9]|[1-9][0-9]|1[0-9][0-9]|2[0-4][0-9]|25[0-5])\.([0-9]|[1-9][0-9]|1[0-9][0-9]|2[0-4][0-9]|25[0-5])\.([0-9]|[1-9][0-9]|1[0-9][0-9]|2[0-4][0-9]|25[0-5])\.([0-9]|[1-9][0-9]|1[0-9][0-9]|2[0-4][0-9]|25[0-5])$"
        return bool(re.match(regexPattern, ipStr))
        

sqlite3.register_adapter(IpAddress, IpAddress.int)
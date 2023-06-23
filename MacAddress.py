import sqlite3, re


class InvalidMacException(Exception):


    def __init__(self, mac):
        super().__init__(f"{mac} is not a valid MAC address.")


class MacAddress:


    def __init__(self, mac):
        if isinstance(mac, float) or isinstance(mac, int):
            if not self.check_int(mac):
                raise InvalidMacException(mac)
            self.int = mac
            macHex = "{:012x}".format(mac)
            self.str = ":".join(macHex[i:i+2] for i in range(0, len(macHex), 2))

        elif isinstance(mac, str):
            mac = mac.lower()
            if not self.check_str(mac):
                raise InvalidMacException(mac)
            self.int = int(mac.replace(":", ""), 16)
            self.str = mac
        
        elif isinstance(mac, MacAddress):
            self = mac
        else:
            raise InvalidMacException(mac)


    def __eq__(self, other):
        return self.str == other.str


    def __hash__(self):
        return hash(self.str)
        

    @staticmethod
    def int(macAddress) -> int:
        return macAddress.to_int()
    

    def to_int(self) -> int:
        return self.int


    def __str__(self) -> str:
        return self.str


    def check_int(self, macInt) -> bool:
        return False if macInt > 2**48 -1 or macInt < 0 else True


    def check_str(self, macStr) -> bool:
        return bool(re.match("[0-9a-f]{2}([:]?)[0-9a-f]{2}(\\1[0-9a-f]{2}){4}$", macStr.lower()))
        

sqlite3.register_adapter(MacAddress, MacAddress.int)
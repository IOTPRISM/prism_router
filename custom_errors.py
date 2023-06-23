class UnknownCommandException(Exception):
    def __init__(self, cmd):
        super().__init__(cmd + " is not a supported command.")

class DeviceNotInDatabaseError(Exception):
    def __init__(self, ip):
        super().__init__(f"Device with ip lease {ip} is not in database")

class DevicesNotLoadedError(Exception):
    pass
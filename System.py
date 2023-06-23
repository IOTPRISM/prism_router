from Shell import Shell
import logging
from utils import is_valid_passphrase


class System:
    

    def __init__(self, shell = None) -> None:
        self.shell = Shell() if shell == None else shell
        self._load_info()
        logging.debug(f"""Loading system information, cpu usage: {self.cpu}, mem usage: 
                         {self.mem}, temp: {self.temp}°C, disk usage: {self.diskUsage}.""")
    

    def _load_info(self) -> None:
        self.cpu = self._cpu_usage()
        self.mem = self._mem_usage()
        self.temp = self._temp()
        self.diskUsage = self._disk_usage()
        self.username = self.shell.execute("nvram get iotrimmer_user")[0]
        self.password = self.shell.execute("nvram get iotrimmer_passwd")[0]
        
        
    def set_login_password(self, password : str) -> None:
        if self.password == password:
            return
        if not is_valid_passphrase(password) or any(not c.isalnum() for c in password):
            logging.error("Invalid IoTrimmer password setting attempted")
            return
        self.shell.execute(f"nvram set iotrimmer_passwd={password}")
        logging.info("new iotrimmer password set")
        self.password = password
        self.shell.execute(f"setuserpasswd {self.username} {self.password}")
    

    def set_login_username(self, username : str) -> None:
        if self.username == username:
            return
        if any(not c.isalnum() for c in username):
            logging.error("Invalid Iotrimmer username setting attempted")
            return
        self.shell.execute(f"nvram set iotrimmer_user={username}")
        logging.info("new IoTrimmer Username set")
        self.username = username
        self.shell.execute(f"setuserpasswd {self.username} {self.password}")
        

    def _cpu_usage(self) -> str:
        res = self.shell.execute("cat /proc/stat")[0].split()
        system = int(res[1])
        user = int(res[3])
        idle = int(res[4])
        percent = (system + user) * 100 / (system + user + idle)
        return str(round(percent, 2)) + ' %'
    
    
    def _mem_usage(self) -> str:
        res = self.shell.execute("cat /proc/meminfo")[1].split()
        total = res[1]
        used = res[2]
        percent = int(used) * 100 / int(total)
        return str(round(percent, 2)) + ' %'


    def _temp(self):
        bash = "cat /sys/class/thermal/thermal_zone*/temp"
        temp = float(self.shell.execute(bash)[-1]) / 1000
        return round(temp, 2)
 
 
    def _disk_usage(self):
        res = self.shell.execute("df -h /dev/sda | tail -1")[0].split()
        total = float(res[1][:-1])
        free = float(res[3][:-1])
        used = 100 - (free / total * 100)
        return str(round(used, 2)) + ' %'

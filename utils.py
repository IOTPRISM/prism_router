import functools, operator, re
from MacAddress import MacAddress


def get_macs_from_str(input_string : str) -> list:
    macCheck = re.compile(r'(?:[0-9a-fA-F]:?){12}')
    return list(map(MacAddress, re.findall(macCheck, input_string)))
    
    
def is_valid_passphrase(password : str) -> bool:
    if ' ' in password:
        return False
    length = len(password)
    return False if length < 8 or length > 32 else True        
     

def is_valid_ssid(ssid : str) -> bool:
    length = len(ssid)
    return True if length > 2 and length < 32 else False


def is_mac(mac : str) -> bool:
    return bool(re.match("[0-9a-f]{2}([:]?)[0-9a-f]{2}(\\1[0-9a-f]{2}){4}$", mac.lower()))

        
def flatten_nested_list(nestedList : list) -> list:
    return functools.reduce(operator.iconcat, nestedList, [])


def is_valid_hex_code(colour : str) -> bool:
    return bool(re.search(r'^#(?:[0-9a-fA-F]{3}){1,2}$', colour))
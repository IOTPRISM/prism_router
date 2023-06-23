import logging, sys
from mac_vendor_lookup import MacLookup
from MacAddress import MacAddress


class VendorLookup:


    def find_vendor(self, mac : MacAddress) -> str:
        try:
            prediction =  str(MacLookup().lookup(mac.__str__()))
            logging.info(f"Predicted vendor for device with mac: {mac}. Predicted vendor: {prediction}.")
        except KeyError:
            prediction =  None
            logging.warning(f"Vendor lookup prediction failed for device with. mac: {mac}.")
        finally:
            return prediction


if __name__ == "__main__":
    print(VendorLookup().find_vendor(sys.argv[1]))
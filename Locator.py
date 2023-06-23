import socket, logging, sqlite3
from geoip2.webservice import Client
from geoip2.errors import OutOfQueriesError, AddressNotFoundError
from DictObj import DictObj


CLIENT = 619197


class Locator:


    def __init__(self, apiKeyFile = '/opt/iotrimmer/maxmind.key') -> None:
        logging.debug(f"Initisalising Locator object with API key {apiKeyFile}.")
        with open(apiKeyFile, "r") as f:
            self.key = f.readlines()[0].strip()


    def locate_and_save(self, destination : str, cur : sqlite3.Cursor) -> None:
        self.cur = cur
        self.destination = destination
        self._find_location()
        self._save()


    def _find_location(self) -> None:
        self.lat, self.long, self.iso, self.identified = None, None, None, 0
        try:
            client = Client(CLIENT, self.key, host='geolite.info')
            response = client.city(socket.gethostbyname(self.destination))
            self.lat = response.location.latitude
            self.long = response.location.longitude
            self.iso = response.country.iso_code
            self.identified = 1
            logging.info(f"Identified location of {self.destination}. Iso code : {self.iso}")
        except OutOfQueriesError:
            self.identified = None
            logging.error(f"Maxmind API is output of queries for client: {CLIENT} and API key: {self.apiKeyFile}.")
        except socket.gaierror:
            logging.warning(f"Address {self.destination} could not be resolved.")
            pass
        except AddressNotFoundError:
            logging.warning(f"Address {self.destination} not found in Maxmind database.")
            pass

    
    def _save(self) -> None:
        # if destination is not in database, ignore other wise insert
        sqlString = """ INSERT OR IGNORE INTO
                                    destination (name, iso_code, latitude, longitude, location_identified)
                                VALUES
                                    (:name, :iso, :lat, :long, :identified);"""
        data = {"iso": self.iso, 
                "lat": self.lat,
                "long": self.long,
                "identified": self.identified,
                "name": self.destination}
        self.cur.execute(sqlString, data)
        # if destination is in database, update.
        sqlString = """ UPDATE 
                            destination 
                        SET 
                            iso_code = :iso, latitude = :lat, longitude = :long, location_identified = :identified
                        WHERE
                            name = :name;"""
        self.cur.execute(sqlString, data)
        logging.debug(f"Saving location of {self.destination} to database.")


class Location(DictObj):


    def __init__(self, dictionary):
        for k in dictionary.keys():
            if k not in ["latitude", "longitude", "count", "normalised", "iso_code"]:
                raise AttributeError
        DictObj.__init__(self, dictionary)


    def normalise(self, minL :float, maxL :float, minV :float, maxV :float):
        try:
            self.normalised = (maxV - minV) * \
                ((self.count - minL) / (maxL - minL)) + minV
        except ZeroDivisionError:
            self.normalised = (maxV + minV) / 2
        finally:
            return self


    def to_normalised_list(self) -> list:
        return [float(self.latitude), float(self.longitude), self.normalised]

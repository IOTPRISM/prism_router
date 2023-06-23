import json, requests, logging, sqlite3, sys, time, hashlib
from datetime import timedelta
from collections import Counter
from MacAddress import MacAddress
from Database import Database
#vs451 changed fropm 64
HASH_RES = 32
API_URL = 'http://127.0.0.1:5000/identify'
TIME_INTERVAL = 30


class DeviceClassifier():


    def _retreive_sld_queries(self, mac : MacAddress, cur : sqlite3.Cursor) -> list:
        sqlString = """ SELECT
                            destination, time
                        FROM
                            queried
                        WHERE
                            mac = ?
                        ORDER BY
                            time ;"""
        cur.execute(sqlString, (mac, ))
        soonest = cur.fetchone()
        queries = [soonest["destination"].split('.')[-2]]
        minTime = Database.convert_time_string(soonest["time"])
        maxTime = minTime + timedelta(seconds=TIME_INTERVAL)
        for query in cur.fetchall():
            if Database.convert_time_string(query["time"]) > maxTime:
                break
            queries.append(query["destination"].split('.')[-2])
        
        dns_count_dict = Counter(queries)
        dns_count = list(dns_count_dict.items())

        def find_sld_freq(dns_count : tuple) -> tuple:
            hasher = hashlib.sha1()
            sld = dns_count[0].encode('utf-8')
            hasher.update(sld)
            hashed = int(hasher.hexdigest(), 16) % HASH_RES
            freq = dns_count[1] / TIME_INTERVAL
            return (hashed, freq)

        return list(map(find_sld_freq, dns_count))


    def _generate_data_point(self, sld_freq : list) -> list:
        dp = [0.0 for _ in range(HASH_RES)]
        for hash, freq in sld_freq:
            dp[hash] = freq 
        return dp
        

    def classify_device(self, mac :MacAddress, cur :sqlite3.Cursor) -> str:
        #vs451 commented below
        #time.sleep(TIME_INTERVAL)
        sld_freq = self._retreive_sld_queries(mac, cur)
        data = self._generate_data_point(sld_freq)
        print(data)
        header = {'Content-Type':'application/json'}
        try:
            response = requests.post(API_URL, headers = header, data = json.dumps(data))
            if response.status_code != 200:
                raise requests.exceptions.ConnectionError
            product = response.content.decode()[2:-2]
            logging.info(f"Classified device with MAC address: {mac} as {product}.")
        except requests.exceptions.ConnectionError:
            logging.error(f"Unable to query server for device identification, connection failed.")
            product = None
        return product

    
if __name__ == "__main__":
    with Database('iotrimmer.db') as cur:    
        print(DeviceClassifier().classify_device(sys.argv[1], cur))


import sqlite3


class Products:
    

    def __init__(self, cur : sqlite3.Cursor):
        self.cur = cur
        self.products = {}
        self.blockedList = {}
        sqlString = """ SELECT
                            name, vendor
                        FROM
                            product
                        ORDER BY
                            name; """
    
        for d in self.cur.execute(sqlString):
            name = d['name'].replace('-', ' ').title()
            self.products[name] = d['vendor']
    

    def load_blocked(self) -> None:
        sqlString = """ SELECT
                    destination
                FROM
                    blocklist
                WHERE
                    product = :product ; """
        for p in self.products:
            blocked = self.cur.execute(sqlString, {"product" : p})
            self.blockedList[p] = [b['destination'] for b in blocked]

    
    def get(self) -> list:
        return list(self.products)


    def get_blocked(self, name : str) -> list:
        if name in self.products:
            return self.blockedList[name]
        else: 
            return []

    def enumerate_blocked(self, name : str) -> list:
        if name in self.products:
            return enumerate(self.blockedList[name])
        else: 
            return []

import sys, os, sqlite3
import unittest
from testing_utils import initialise_test_database, populate_test_database, DB_TEST_FILE
sys.path.append('../')
from Database import Database
from Shell import Shell


class DatabaseTest(unittest.TestCase):


    def test_check_error_if_no_db(self):
        with self.assertRaises(FileNotFoundError):
            with Database(dbFile='nope'):
                pass


    def test_returns_cursor(self):
        with Database(dbFile=DB_TEST_FILE) as cur:
            self.assertEqual(type(cur), sqlite3.Cursor)


    def test_check_dict_cursor(self):
        db = Database(dbFile=DB_TEST_FILE)
        with db:
            self.assertEqual(db.conn.row_factory, sqlite3.Row)
        db = Database(dbFile=DB_TEST_FILE, dictCursor=False)
        with db:
            self.assertEqual(db.conn.row_factory, None)


    def test_connection_closes_after_use(self):
        db = Database(dbFile=DB_TEST_FILE)
        with db as cur:
            pass
        with self.assertRaises(sqlite3.ProgrammingError):
            cur.execute("query")


    def test_duplicate_database_creation_fails(self):
        db = Database(dbFile = DB_TEST_FILE)
        with self.assertRaises(FileExistsError):
            db.create_database()


    def test_database_creation_succeeds(self):
        tempTest = 'one_time_test.db'
        db = Database(dbFile=tempTest)
        db.create_database()
        sqlString = "SELECT * FROM block_allow;"
        try:
            with db as cur:
                cur.execute(sqlString)
        finally:
            os.remove(tempTest)


    def test_clear_database(self):
        populate_test_database(DB_TEST_FILE)
        db = Database(dbFile=DB_TEST_FILE)
        db.clear_database()
        # get list of tables
        getTables = """ SELECT
                    name
                FROM
                    sqlite_master
                WHERE
                    type='table';"""
        with db as cur:
        # check tables are empty
            for t in cur.execute(getTables):
                getCount = f"SELECT count(*) FROM {t[0]};"
                cur.execute(getCount)
                self.assertFalse(cur.fetchone()[0])


    def test_database_size(self):
        db = Database(dbFile=DB_TEST_FILE)
        self.assertEqual(type(db.size(Shell())), int)


    def test_database_version(self):
        initialise_test_database(DB_TEST_FILE)
        db = Database(dbFile=DB_TEST_FILE)
        self.assertEqual(db.version(), 0)


    def test_database_metrics(self):
        populate_test_database(DB_TEST_FILE)
        db = Database(dbFile=DB_TEST_FILE)
        self.assertEqual(db.metrics()["totalDestCount"], 100)
        self.assertEqual(db.metrics()["uniqueDestCount"], 100)
        self.assertEqual(db.metrics()["blockedCount"], 50)


    def test_database_metrics_when_db_empty(self):
        initialise_test_database(DB_TEST_FILE)
        db = Database(dbFile=DB_TEST_FILE)
        self.assertEqual(db.metrics()["totalDestCount"], 0)
        self.assertEqual(db.metrics()["uniqueDestCount"], 0)
        self.assertEqual(db.metrics()["blockedCount"], 0)

if __name__ == '__main__':
    unittest.main()
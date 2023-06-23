import sys, unittest
sys.path.append('../')
from testing_utils import initialise_test_database, populate_test_database, DB_TEST_FILE
from Traffic import TrafficMetrics
from Database import Database


class TrafficMetricsTests(unittest.TestCase):


    def test_initialisation_on_populated_database(self):
        populate_test_database(DB_TEST_FILE)
        db = Database(dbFile=DB_TEST_FILE)
        with db as cur:
            traffic = TrafficMetrics(cur)
            self.assertAlmostEqual(traffic.totalQueried, 100)
            self.assertAlmostEqual(traffic.totalBlocked, 100)
            self.assertAlmostEqual(traffic.percentageBlocked, 100)


    def test_initialisation_on_unpopulated_database(self):
        initialise_test_database(DB_TEST_FILE)
        db = Database(dbFile=DB_TEST_FILE)
        with db as cur:
            traffic = TrafficMetrics(cur)
            self.assertEqual(traffic.totalQueried, 0)
            self.assertEqual(traffic.totalBlocked, 0)
            self.assertEqual(traffic.percentageBlocked, 0)
            self.assertEqual(traffic.thirdSupportPercentageBlocked, 0)


if __name__ == "__main__":
    unittest.main()

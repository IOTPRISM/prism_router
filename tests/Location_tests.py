import sys
sys.path.append('../')
import unittest
from Locator import Location

class LocationTest(unittest.TestCase):

    def test_assignment_works(self):
        dic = { "latitude":0.5,
                "longitude": 2.6,
                "count":1}
        l = Location(dic)
        self.assertEqual(l.latitude, l["latitude"])
        self.assertEqual(l.longitude, l["longitude"])
        self.assertEqual(l.count, l["count"])
        self.assertEqual(l.latitude, 0.5)
        self.assertEqual(l.longitude, 2.6)
        self.assertEqual(l.count, 1)


    def test_normalisation(self):
        l = Location({"count":1})
        l.normalise(1, 10, 10, 20)
        self.assertEqual(l.normalised, 10)
        l.normalise(0, 1, 10, 20)
        self.assertEqual(l.normalised, 20)


    def test_to_normalised_list(self):
        dic = { "latitude":0.5,
                "longitude": 2.6,
                "count":1}
        l = Location(dic)
        l.normalise(1, 10, 10, 20)
        self.assertEqual(l.to_normalised_list(), [0.5, 2.6, 10])

        
if __name__ == '__main__':
    unittest.main()
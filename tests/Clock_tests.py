import sys, unittest
from datetime import datetime
sys.path.append('../')
from Clock import Clock

class ShellTest(unittest.TestCase):

    def test_clock_initialisation(self):
        cl = Clock()
        self.assertEqual(len(cl.times), 144)
        self.assertTrue(all(map(lambda t : type(t) == datetime, cl.times)))

    def test_clock_print_list(self):
        self.assertTrue(all(map(lambda t : type(t) == str, Clock().print_time_list())))

if __name__ == "__main__":
    unittest.main()
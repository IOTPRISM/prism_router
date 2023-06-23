import sys
sys.path.append('../')
from InterfaceColor import InterfaceColor
import unittest

TEST_CSS_FILE = "style.css.test"

def get_color_from_file():
    with open(TEST_CSS_FILE, 'r') as file:
        return file.readlines()[1][17:-2]

class InterfaceColorTest(unittest.TestCase):

    def test_setting_color(self):
        self.assertEqual(get_color_from_file(), "#e30073")
        ifcol = InterfaceColor(file = TEST_CSS_FILE)
        ifcol.set_color("#e30074")
        self.assertEqual(get_color_from_file(), "#e30074")
        ifcol.set_color("#e30073")
        self.assertEqual(get_color_from_file(), "#e30073")


    def test_setting_incorrect_color(self):
        ifcol = InterfaceColor(file = TEST_CSS_FILE)
        ifcol.set_color("#notahexcode")
        self.assertEqual(get_color_from_file(), "#e30073")
        

if __name__ == "__main__":
    unittest.main()

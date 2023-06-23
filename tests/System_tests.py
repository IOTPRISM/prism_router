import sys
import unittest
from unittest.mock import Mock
sys.path.append('../')
from System import System

CONSTRUCTOR_SHELL_OUTPUT = [
                            ["cpu  19501 0 13857 28719709 292 0 5971 0 0 0"],
                            ["        total:    used:    free:  shared: buffers:  cached:",
                             "Mem:  523100160 273371136 249729024        0 19468288 42262528"],
                            ["80355"],
                            ["/dev/sda1               112.8G    364.1M    106.7G   0% /opt"]
                            ]

class SystemTest(unittest.TestCase):

    def test_values_are_set_correctly(self):
        mockShell = Mock()
        mockShell.execute.side_effect=CONSTRUCTOR_SHELL_OUTPUT
        systm = System(shell=mockShell)
        self.assertEqual(systm.cpu, "0.12 %")
        self.assertEqual(systm.diskUsage, "5.41 %")
        self.assertEqual(systm.mem, "52.26 %")
        self.assertEqual(systm.temp, 80.36)


if __name__ == "__main__":
    unittest.main()

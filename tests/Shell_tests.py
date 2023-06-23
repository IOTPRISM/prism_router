import sys
import unittest
sys.path.append('../')
from Shell import Shell

class ShellTest(unittest.TestCase):

    def test_shell_execute(self):
        sh = Shell()
        bash = "echo test && echo test2 && echo test3"
        output = sh.execute(bash)
        self.assertEqual(output, ["test", "test2", "test3"])

if __name__ == "__main__":
    unittest.main()

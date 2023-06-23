import sys
sys.path.append('../')
from DictObj import DictObj
import unittest

class DictObjTest(unittest.TestCase):
    def test_assignemnt_of_attributes(self):
        dictionary = {"A":"a", "B":"b"}
        d = DictObj(dictionary)
        self.assertEqual(d.A, "a")
        self.assertEqual(d["A"] ,"a")
        d.A = "b"
        self.assertEqual(d.A,"b")
        self.assertEqual(d["A"], "b")
        d.B = "a"
        self.assertEqual(d.B, "a")
        self.assertEqual(d["B"], "a")
        d["A"] = "b"
        self.assertEqual(d.A,"b")
        self.assertEqual(d["A"], "b")
        d["b"] = "a"
        self.assertEqual(d.B, "a")
        self.assertEqual(d["B"], "a")

    def test_dict___str__method(self):
        dictionary = {"A":"a", "B":"b"}
        d = DictObj(dictionary)
        self.assertEqual(str(d), "{'A': 'a', 'B': 'b'}")

if __name__ == "__main__":
    unittest.main()

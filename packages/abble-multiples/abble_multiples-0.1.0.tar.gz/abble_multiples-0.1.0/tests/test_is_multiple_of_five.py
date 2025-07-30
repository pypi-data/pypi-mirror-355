import unittest
import sys
import os

sys.path.insert(0, os.path.abspath(os.path.join(os.path.dirname(__file__), '..')))
from multiples.is_multiple_of_five import is_multiple_of_five

class TestIsMultipleOfFive(unittest.TestCase):
    def test_is_multiple_of_five(self):
        self.assertTrue(is_multiple_of_five(75))

if __name__ == '__main__':
    unittest.main()

import numpy as np
import unittest
from pySciTools.utils import func1, func2


class TestUtils(unittest.TestCase):

  def test_func1(self):
    data = [1, 2, 3]
    result = func1(data)
    self.assertTrue(isinstance(result, np.ndarray))

  def test_func2(self):
    result = func2(2, 3)
    self.assertEqual(result, 5)


if __name__ == '__main__':
  unittest.main()

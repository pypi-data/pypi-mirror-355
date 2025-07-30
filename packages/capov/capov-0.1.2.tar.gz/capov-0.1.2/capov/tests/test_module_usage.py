import unittest
import os
from capov.fixers import process

class TestModuleUsage(unittest.TestCase):

  def setUp(self):
    self.code = '''
import os
import os

def func():
  return math.sqrt(4)

def other():
  return datetime.now()

data = [1,2,3,]
x = (5 + 3
print(json.dumps(data))
'''

  def test_process_all_features(self):
    result = process(self.code, revise=True)
    self.assertIn("import json", result)
    self.assertIn("import math", result)
    self.assertIn("from datetime import datetime", result)
    self.assertNotIn("import os\nimport os", result)
    self.assertNotIn(",]", result)
    self.assertTrue(result.count('(') == result.count(')'))

if __name__ == '__main__':
  unittest.main()
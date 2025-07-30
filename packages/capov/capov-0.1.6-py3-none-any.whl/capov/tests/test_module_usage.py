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

  def test_repair_all_features(self):
    print("\n=== Running test: Repair all faulty features ===")

    print("Step 1: Processing code...")
    result = process(self.code)

    print("Step 2: Checking for required imports...")
    assert "import json" in result, "Missing import: json"
    assert "import math" in result, "Missing import: math"
    assert "from datetime import datetime" in result, "Missing import: datetime"
    print("OK: All required imports found.")

    print("Step 3: Checking for duplicate imports...")
    assert "import os\nimport os" not in result, "Duplicate import not removed"
    print("OK: Duplicate import removed.")

    print("Step 4: Checking for trailing commas...")
    assert ",]" not in result, "Trailing comma in list not fixed"
    print("OK: Trailing commas handled.")

    print("Step 5: Checking parentheses...")
    assert result.count('(') == result.count(')'), "Unbalanced parentheses"
    print("OK: Parentheses are balanced.")

    print("\nProcessed result (final):\n", result)
    print("\n✅ SUCCESS: All feature repairs validated.")

if __name__ == '__main__':
  unittest.main()
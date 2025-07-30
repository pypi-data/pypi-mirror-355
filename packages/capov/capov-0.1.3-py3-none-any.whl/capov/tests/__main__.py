import unittest
import os
import sys

if __name__ == '__main__':
  print("Running CapOv test suite...\n")
  test_dir = os.path.dirname(__file__)
  suite = unittest.defaultTestLoader.discover(start_dir=test_dir, pattern='test_*.py')
  runner = unittest.TextTestRunner(verbosity=2, buffer=False)
  result = runner.run(suite)

  if not result.wasSuccessful():
    sys.exit(1)
  print("\nAll tests completed successfully.")
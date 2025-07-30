import unittest
import subprocess
import os
import shutil

class TestFullCLI(unittest.TestCase):
  base   = "capov/tests/faulty_scripts/faulty_full_combo_case.py"
  tmp    = "capov/tests/tmp_full_combo.py"
  output = "capov/tests/tmp_output.py"
  log    = "capov/tests/tmp_log.txt"

  def setUp(self):
    with open(self.base, 'w') as f:
      f.write('''import os\nimport os\n\ndef func():\n  return math.sqrt(4)\n\ndef other():\n  return datetime.now()\n\ndata = [1,2,3,]\nx = (5 + 3\nprint(json.dumps(data))''')
    shutil.copy2(self.base, self.tmp)

  def tearDown(self):
    for path in [self.base, self.tmp, self.output, self.log, self.tmp + ".bak"]:
      try:
        os.remove(path)
      except FileNotFoundError:
        pass

  def test_full_cli_usage(self):
    # First run: test in-place edit with backup, verbose, log
    subprocess.run([
      "python3", "-m", "capov", self.tmp,
      "--in-place", "--backup", "--verbose", "--log", self.log
    ], capture_output=True, text=True)

    self.assertTrue(os.path.exists(self.tmp))
    self.assertTrue(os.path.exists(self.tmp + ".bak"))
    self.assertTrue(os.path.exists(self.log))

    with open(self.tmp) as f:
      content = f.read()
      self.assertIn("import json", content)
      self.assertIn("import math", content)
      self.assertIn("from datetime import datetime", content)
      self.assertNotIn(",]", content)
      self.assertTrue(content.count('(') == content.count(')'))

    # Second run: test writing to output file only
    shutil.copy2(self.base, self.tmp)
    subprocess.run([
      "python3", "-m", "capov", self.tmp,
      "--output", self.output
    ], capture_output=True, text=True)

    self.assertTrue(os.path.exists(self.output))
    with open(self.output) as f:
      out = f.read()
      self.assertIn("import json", out)
      self.assertIn("import math", out)
      self.assertIn("from datetime import datetime", out)
      self.assertNotIn(",]", out)
      self.assertTrue(out.count('(') == out.count(')'))

if __name__ == '__main__':
  unittest.main()


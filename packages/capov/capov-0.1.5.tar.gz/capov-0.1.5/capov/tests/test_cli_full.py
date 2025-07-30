import importlib.resources as res
import subprocess
import unittest
import shutil
import os


class TestFullCLI(unittest.TestCase):
  base_name = "faulty_full_combo_case.py"
  tmp       = "capov/tests/tmp_full_combo.py"
  output    = "capov/tests/tmp_output.py"
  log       = "capov/tests/tmp_log.txt"

  def setUp(self):
    print("\n=== Setting up test: Full CLI test ===")
    with res.path("capov.tests.faulty_scripts", self.base_name) as p:
      self.base = str(p)
    with open(self.base, 'w') as f:
      f.write('''import os\nimport os\n\ndef func():\n  return math.sqrt(4)\n\ndef other():\n  return datetime.now()\n\ndata = [1,2,3,]\nx = (5 + 3\nprint(json.dumps(data))''')
    shutil.copy2(self.base, self.tmp)

  def tearDown(self):
    print("Cleaning up test artifacts...")
    for path in [self.base, self.tmp, self.output, self.log, self.tmp + ".bak"]:
      try:
        os.remove(path)
        print("Deleted:", path)
      except FileNotFoundError:
        pass

  def test_full_cli_usage(self):
    print("\n--- Running test_full_cli_usage ---")

    print("Step 1: --in-place with backup, verbose, log")
    subprocess.run([
      "python3", "-m", "capov", self.tmp,
      "--in-place", "--backup", "--verbose", "--log", self.log
    ], capture_output=True, text=True)

    assert os.path.exists(self.tmp)
    assert os.path.exists(self.tmp + ".bak")
    assert os.path.exists(self.log)

    with open(self.tmp) as f:
      content = f.read()
      print("\nValidating in-place edited content:\n", content)
      assert "import json" in content
      assert "import math" in content
      assert "from datetime import datetime" in content
      assert ",]" not in content
      assert content.count('(') == content.count(')')
    print("OK: First CLI usage passed.")

    print("\nStep 2: Re-run with output file")
    shutil.copy2(self.base, self.tmp)
    subprocess.run([
      "python3", "-m", "capov", self.tmp,
      "--output", self.output
    ], capture_output=True, text=True)

    assert os.path.exists(self.output)
    with open(self.output) as f:
      out = f.read()
      print("\nValidating output file content:\n", out)
      assert "import json" in out
      assert "import math" in out
      assert "from datetime import datetime" in out
      assert ",]" not in out
      assert out.count('(') == out.count(')')
    print("OK: Output file test passed.")

    print("SUCCESS: test_full_cli_usage completed successfully.")

if __name__ == '__main__':
  unittest.main()

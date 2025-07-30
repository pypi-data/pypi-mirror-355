import unittest
import subprocess
import os
import shutil


class TestCapOvCLI(unittest.TestCase):
  base_path = "capov/tests/faulty_scripts/faulty_imports_inside_func.py"
  tmp_path  = "capov/tests/tmp_faulty_copy.py"

  def setUp(self):
    shutil.copy2(self.base_path, self.tmp_path)

  def tearDown(self):
    for suffix in ["", ".bak", ".orig"]:
      try:
        os.remove(self.tmp_path + suffix)
      except FileNotFoundError:
        pass
    for tmp in ["capov/tests/tmp_output.py", "capov/tests/tmp_log.txt"]:
      try:
        os.remove(tmp)
      except FileNotFoundError:
        pass

  def _validate_output(self, output_text):
    self.assertIn("import math", output_text)
    self.assertIn("from datetime import datetime", output_text)

  def test_stdout(self):
    result = subprocess.run(["python3", "-m", "capov", self.tmp_path], capture_output=True, text=True)
    self.assertEqual(result.returncode, 0)
    self._validate_output(result.stdout)

  def test_output_file(self):
    subprocess.run(["python3", "-m", "capov", self.tmp_path, "--output", "capov/tests/tmp_output.py"])
    self.assertTrue(os.path.exists("capov/tests/tmp_output.py"))
    with open("capov/tests/tmp_output.py") as f:
      self._validate_output(f.read())

  def test_in_place_backup(self):
    subprocess.run(["cp", self.tmp_path, self.tmp_path + ".orig"])
    subprocess.run(["python3", "-m", "capov", self.tmp_path, "--in-place", "--backup"])
    self.assertTrue(os.path.exists(self.tmp_path + ".bak"))
    with open(self.tmp_path) as f:
      self._validate_output(f.read())

  def test_verbose_log(self):
    log_path = "capov/tests/tmp_log.txt"
    result = subprocess.run([
      "python3", "-m", "capov", self.tmp_path,
      "--in-place", "--verbose", "--log", log_path
    ], capture_output=True, text=True)
    self.assertIn("Loaded", result.stdout)
    with open(self.tmp_path) as f:
      self._validate_output(f.read())

if __name__ == '__main__':
  unittest.main()


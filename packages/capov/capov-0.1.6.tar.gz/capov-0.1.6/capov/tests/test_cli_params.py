import importlib.resources as res
import subprocess
import unittest
import tempfile
import shutil
import os


class TestCapOvCLI(unittest.TestCase):
  base_name = "faulty_imports_inside_func.py"

  def setUp(self):
    print("\n=== Setting up test: CLI tests ===")
    self.tmp_dir = tempfile.gettempdir()
    self.tmp_path = os.path.join(self.tmp_dir, "tmp_faulty_copy.py")
    print("Copying test file to:", self.tmp_path)
    with res.path("capov.tests.faulty_scripts", self.base_name) as p:
      shutil.copy2(str(p), self.tmp_path)

  def tearDown(self):
    print("Cleaning up test artifacts...")
    for suffix in ["", ".bak", ".orig"]:
      try:
        os.remove(self.tmp_path + suffix)
        print("Deleted:", self.tmp_path + suffix)
      except FileNotFoundError:
        pass
    for tmp_name in ["tmp_output.py", "tmp_log.txt"]:
      tmp = os.path.join(self.tmp_dir, tmp_name)
      try:
        os.remove(tmp)
        print("Deleted:", tmp)
      except FileNotFoundError:
        pass

  def _validate_output(self, output_text):
    print("\nValidating output:\n", output_text)
    print("Checking for required import statements...")
    assert "import math" in output_text, "Missing: import math"
    assert "from datetime import datetime" in output_text, "Missing: from datetime import datetime"
    print("OK: Required imports present.")

  def test_stdout(self):
    print("\n--- Running CLI test: stdout mode ---")
    result = subprocess.run(["python3", "-m", "capov", self.tmp_path], capture_output=True, text=True)
    print("Return code:", result.returncode)
    print("STDOUT:\n", result.stdout)
    assert result.returncode == 0
    self._validate_output(result.stdout)
    print("SUCCESS: CLI stdout mode passed.")

  def test_output_file(self):
    print("\n--- Running CLI test: --output mode ---")
    output_path = os.path.join(self.tmp_dir, "tmp_output.py")
    subprocess.run(["python3", "-m", "capov", self.tmp_path, "--output", output_path])
    assert os.path.exists(output_path)
    with open(output_path) as f:
      self._validate_output(f.read())
    print("SUCCESS: CLI --output mode passed.")

  def test_in_place_backup(self):
    print("\n--- Running CLI test: --in-place with --backup ---")
    subprocess.run(["cp", self.tmp_path, self.tmp_path + ".orig"])
    subprocess.run(["python3", "-m", "capov", self.tmp_path, "--in-place", "--backup"])
    assert os.path.exists(self.tmp_path + ".bak")
    with open(self.tmp_path) as f:
      self._validate_output(f.read())
    print("SUCCESS: CLI --in-place with --backup passed.")

  def test_verbose_log(self):
    print("\n--- Running CLI test: --verbose --log ---")
    log_path = os.path.join(self.tmp_dir, "tmp_log.txt")
    result = subprocess.run([
      "python3", "-m", "capov", self.tmp_path,
      "--in-place", "--verbose", "--log", log_path
    ], capture_output=True, text=True)
    print("Return code:", result.returncode)
    print("STDOUT:\n", result.stdout)
    assert "Loaded" in result.stdout
    with open(self.tmp_path) as f:
      self._validate_output(f.read())
    print("SUCCESS: CLI --verbose --log passed.")

if __name__ == '__main__':
  unittest.main()
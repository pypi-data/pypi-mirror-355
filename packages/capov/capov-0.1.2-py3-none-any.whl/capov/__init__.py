def test(verbose=False):
  import subprocess
  import os
  import sys

  test_dir = os.path.join(os.path.dirname(__file__), "tests")
  if not os.path.exists(test_dir):
    print("[CapOv] Tests not available in this installation.")
    return

  cmd = ["pytest", test_dir]
  if verbose:
    cmd.append("-v")

  print(f"[CapOv] Running: {' '.join(cmd)}")
  result = subprocess.call(cmd)
  if result != 0:
    sys.exit(result)
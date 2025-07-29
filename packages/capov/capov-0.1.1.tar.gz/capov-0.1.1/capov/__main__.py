import sys
import argparse
import shutil
import os
from capov.fixers import process

def main():
  parser = argparse.ArgumentParser(description="CapOv - Fix obvious Python bugs")
  parser.add_argument("filepath", help="Path to the Python file to fix")
  parser.add_argument("--in-place", action="store_true", help="Modify the original file in-place")
  parser.add_argument("--output", help="Write output to this file instead of stdout")
  parser.add_argument("--backup", action="store_true", help="Make a .bak backup before overwriting")
  parser.add_argument("--verbose", action="store_true", help="Print debug information")
  parser.add_argument("--log", help="Write log info to the given file")

  args = parser.parse_args()

  try:
    with open(args.filepath, 'r') as f:
      original_code = f.read()
    if args.verbose:
      print(f"[CapOv] Loaded {args.filepath}")

    fixed_code = process(original_code)

    # Handle logging
    if args.log:
      with open(args.log, 'a') as logf:
        logf.write(f"[CapOv] Processed {args.filepath}\n")

    # Handle output
    if args.in_place:
      if args.backup:
        shutil.copy2(args.filepath, args.filepath + ".bak")
        if args.verbose:
          print(f"[CapOv] Backup created at {args.filepath}.bak")
      with open(args.filepath, 'w') as f:
        f.write(fixed_code)
      if args.verbose:
        print(f"[CapOv] Overwritten {args.filepath}")
    elif args.output:
      with open(args.output, 'w') as f:
        f.write(fixed_code)
      if args.verbose:
        print(f"[CapOv] Written to {args.output}")
    else:
      print(fixed_code)

  except Exception as e:
    print(f"[CapOv] Error: {e}")
    sys.exit(1)

if __name__ == "__main__":
  main()
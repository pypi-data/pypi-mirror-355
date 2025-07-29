# CapOv — Captain Obvious

**Fixes the dumbest, most obvious Python code errors automatically.**

CapOv corrects only the 100% safe stuff: missing imports, duplicate imports, unclosed brackets, and more — with zero assumptions.

---

## 🔧 Installation
```bash
pip install capov
```

---

## 🚀 Example usage

```python
from capov.fixers import process

code = '''
import os
import os
x = [1, 2, 3,
print(json.dumps(x)
'''

fixed = process(code, revise=True)
print(fixed)
```

Command-line:
```bash
python -m capov your_script.py [options]
```

Options:
- `--in-place` → Overwrite the input file
- `--output FILENAME` → Write fixed code to a separate file
- `--backup` → Create a `.bak` backup before overwrite
- `--verbose` → Print debug messages
- `--log FILE` → Log to specified log file

---

## 🧪 Run tests

```bash
python -m unittest discover capov/tests
```

---

## 🗂 Project structure

- `capov/` — main package
  - `fixers.py` — bug fixing logic
  - `__main__.py` — CLI entry point
  - `example.py` — example usage
  - `tests/`
    - `test_fixers.py` — function tests
    - `test_cli_params.py` — CLI tests
    - `faulty_scripts/` — broken Python samples (excluded from PyPI)

---

## 📦 Get full package (with tests/examples)

### Option 1: GitHub clone
```bash
git clone https://github.com/HansPeterRadtke/capov.git
cd capov
```

### Option 2: PyPI + extract manually
```bash
pip download capov
mkdir capov_extracted && tar -xzf capov-*.tar.gz -C capov_extracted --strip-components=1
cd capov_extracted
```

---

CapOv is your cleanup butler. Let him sweep the dumb bugs so you don't have to.

> Submit bugs or contribute: https://github.com/HansPeterRadtke/capov


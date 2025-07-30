import autoimport
import ast
import re


def fix_missing_imports(code: str) -> str:
  try:
    return autoimport.fix_code(code)
  except Exception as e:
    return code


def remove_duplicate_imports(code: str) -> str:
  seen   = set()
  result = []
  for line in code.splitlines():
    if  ((line.startswith("import") or line.startswith("from")) and (line in seen)):
      continue
    seen  .add   (line)
    result.append(line)
  return "\n".join(result)


def fix_trailing_commas(code: str) -> str:
  lines = code.split('\n')
  for i, line in enumerate(lines):
    if  (re.search(r',\s*$', line.strip())):
      lines[i] = re.sub(r',\s*$', '', line)
  fixed_code = '\n'.join(lines)
  fixed_code = re.sub(r",\s*\]", "]", fixed_code)
  fixed_code = re.sub(r",\s*\)", ")", fixed_code)
  return fixed_code


def fix_unclosed_brackets(code: str) -> str:
  lines       = code.splitlines()
  fixed_lines = []
  brackets    = {'(': ')', '[': ']', '{': '}'}
  closers     = {')', ']', '}'}
  for line in lines:
    stack = []
    for ch in line:
      if  (ch in brackets):
        stack.append(brackets[ch])
      elif((ch in closers) and stack and (ch == stack[-1])):
        stack.pop()
    fixed_lines.append(line + ''.join(reversed(stack)))
  return '\n'.join(fixed_lines)


def fix_obvious_errors(code: str) -> str:
  code = fix_trailing_commas(code)
  code = fix_unclosed_brackets(code)
  code = fix_missing_imports(code)
  code = remove_duplicate_imports(code)
  return code


def revise_code(code: str) -> str:
  return code


def process(code: str, revise: bool = False) -> str:
  code = fix_obvious_errors(code)
  if revise:
    code = revise_code(code)
  return code


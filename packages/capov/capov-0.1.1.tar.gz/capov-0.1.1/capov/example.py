from capov.fixers import process

code = '''
import os
import os

x = [1, 2, 3,

print(json.dumps(x)
'''

fixed = process(code, revise=True)
print("\n[Fixed Code]\n")
print(fixed)
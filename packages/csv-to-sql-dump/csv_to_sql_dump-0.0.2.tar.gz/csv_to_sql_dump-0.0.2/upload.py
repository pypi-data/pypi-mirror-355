
"""
- finds and increments project version eg. 0.0.4 to 0.0.5 (else version conflict error)
- builds PyPI package locally into dist/* using "python -m build"
- uploads built PyPI package using "python -m twine upload dist/*" (need to key in your API key)

"pip install build twine" if you haven't already
"""
import os
import re
import sys

with open('pyproject.toml') as f:
    text = f.read()

# "python -m upload.py --nowrite" if you don't want this script to increment version in pyproject.toml
if "--nowrite" not in sys.argv:
    print("incrementing version by 1 in pyproject.toml")
    old_version: str = re.findall('version = "(.*?)"', text)[0]     # "0.0.4"
    major, minor, patch = old_version.split('.')                    # major="0" minor="0" patch="4"
    new_patch = int(patch) + 1
    new_version = f'{major}.{minor}.{new_patch}'                    # "0.0.5"
    text = re.sub(old_version, new_version, text)
    with open('pyproject.toml', 'w') as f:
        f.write(text)   

with open('pyproject.toml', 'w') as f:
    f.write(text)    

commands = [
    'rm -rf ./dist',                    # removes current dist folder
    'python3 -m build',                 # build PyPI project
    'python3 -m twine upload dist/*'    # upload to PyPI
]

for command in commands:
    print(command)
    os.system(command)

# setup.py
import shutil
from setuptools import setup

with open("src/smcore/VERSION", "r") as f:
    version = f.read()

version = version.replace("v", "")
res = version.split("-")

# Probably a little brittle, but working for now
# Update: it was brittle
# if len(res) > 1:
#     version = res[0] + ".dev" + res[1] + "+" + res[2]
# else:
#     version = res[0].strip()

setup(version=f"{version}", test_suite="tests")

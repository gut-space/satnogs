#!/usr/bin/env python
import os
from setuptools import setup, find_packages
import shutil
import stat
import sys

REQUIREMENTS = [i.strip() for i in open("requirements.txt").readlines()]

EXTERNAL_DEPENDENCIES = ["noaa-apt", "rtl_fm", "sox", "meteor-demod", "medet", "convert"]

RECIPE_DIR = "recipes"

for dep in EXTERNAL_DEPENDENCIES:
    print('Checking if "%s" is installed...' % (dep,), end="")
    if shutil.which(dep) is None:
        print("MISSING")
        sys.exit(1)
    else:
        print("OK")

for recipe_candidate_name in os.listdir(RECIPE_DIR):
    if not recipe_candidate_name.endswith(".sh"):
        continue
    recipe_path = os.path.join(RECIPE_DIR, recipe_candidate_name)
    st = os.stat(recipe_path)
    os.chmod(recipe_path, st.st_mode | stat.S_IXUSR) 

setup(name='SatNOG PG',
      version='1.0',
      description='Ground station manage tool',
      author='SF, TM',
      packages=find_packages(),
      install_requires=REQUIREMENTS
)

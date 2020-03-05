#!/usr/bin/env python

from setuptools import setup, find_packages
import shutil
import sys

REQUIREMENTS = [i.strip() for i in open("requirements.txt").readlines()]

EXTERNAL_DEPENDENCIES = ["noaa-apt", "rtl_fm", "sox"]

for dep in EXTERNAL_DEPENDENCIES:
    print('Checking if "%s" is installed...' % (dep,), end="")
    if shutil.which(dep) is None:
        print("MISSING")
        sys.exit(1)
    else:
        print("OK")

setup(name='SatNOG PG',
      version='1.0',
      description='Ground station manage tool',
      author='SF, TM',
      packages=find_packages(),
      install_requires=REQUIREMENTS
)

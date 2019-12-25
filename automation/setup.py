#!/usr/bin/env python

from setuptools import setup, find_packages 

setup(name='SatNOG PG',
      version='1.0',
      description='Satelitte station - automation script',
      author='SF, TM',
      packages=find_packages(),
      install_requires=[
          "orbit-predictor>=1.10"
      ]
     )

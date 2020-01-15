#!/usr/bin/env python

from setuptools import setup, find_packages 

setup(name='SatNOG PG',
      version='1.0',
      description='Satelitte station - automation script',
      author='SF, TM',
      packages=find_packages(),
      install_requires=[
          "orbit-predictor>=1.10",
          "DateTimeRange>=0.6",
          "python-crontab>=2.4",
          "cron-descriptor>=1.2.24",
          "PyYAML>=5.3"
      ]
     )

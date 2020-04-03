#!/usr/bin/env python3

from os import getcwd, path
import shutil

from setuptools import setup, find_packages

# STEP 1: install python packages
REQUIREMENTS = [i.strip() for i in open("requirements.txt").readlines()]

setup(name='satnogs-server',
      version='1.0',
      description='satnogs-gut server',
      author='SF, TM',
      packages=find_packages(),
      install_requires=REQUIREMENTS
)

# STEP 2: ensure the config is exists
if not path.exists("satnogs.ini"):
    shutil.copyfile("satnogs.ini.template", "satnogs.ini")

# STEP 3: ensure the database is updated.

from migrate_db import *
migrate()

# STEP 4: make sure the update script will be called every day
COMMENT_UPDATE_TAG = 'satnogs-gut-update'

def install_update_cronjob():
    print("Installing cronjob")
    from crontab import CronTab
    cron = CronTab(user=True)

    # remove old cronjobs (if any)
    cron.remove_all(comment=COMMENT_UPDATE_TAG)

    # This job will pull the new code at noon
    job = cron.new(command="cd " + getcwd() + " && ./update.sh", comment=COMMENT_UPDATE_TAG)
    job.setall('0 12 * * *')

    cron.write()

install_update_cronjob()

print("Installation complete.")

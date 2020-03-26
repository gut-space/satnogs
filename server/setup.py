#!/usr/bin/env python3

from os import getcwd, path

from setuptools import setup, find_packages

REQUIREMENTS = [i.strip() for i in open("requirements.txt").readlines()]

setup(name='satnogs-server',
      version='1.0',
      description='satnogs-gut server',
      author='SF, TM',
      packages=find_packages(),
      install_requires=REQUIREMENTS
)

COMMENT_UPDATE_TAG = 'satnogs-gut-update'

def install_update_cronjob():
    print("Installing cronjob")
    from crontab import CronTab
    cron = CronTab(user=True)

    # remove old cronjobs (if any)
    cron.remove_all(comment=COMMENT_UPDATE_TAG)

    # This job will pull the new code at noon
    job = cron.new(command=path.join(getcwd(),'update.sh'), comment=COMMENT_UPDATE_TAG)
    job.setall('0 12 * * *')

    cron.write()

install_update_cronjob()

print("Installation complete.")

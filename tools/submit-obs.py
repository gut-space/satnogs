#!/usr/bin/python

# This tool is used to upload recorded observations to the on-line database. Usage:
#
# ./submit-ops.py filename sat_name aos [tca] [los] [notes]
#
# filename - name of the PNG file
# aos - timestamp, aquisiton of signal
# tca - timestamp, time of closest approach
# los - timestamp, loss of signal
# sat_name - name of the satellite
# notes - a string with notes

hostname="satnogs.klub.com.pl"
subdir="public_html/data"

import sys
import os
import subprocess

def submit_observation(path, sat_name, aos, tca, los, notes):

    dst = "%s:%s" % (hostname, subdir)
    print("Uploading file: cmd=[scp %s %s]" % (path, dst))
    subprocess.run(["scp", path, dst])

    fnames = path.split("/")
    filename = fnames[-1]

    cmd = "psql -c \"INSERT INTO observations(aos,sat_name,filename) VALUES('%s', '%s', '%s')\"" % (aos, sat_name, filename)
    print("Adding record in the db: cmd=[%s]" % cmd)
    subprocess.run(["ssh", hostname, cmd])


print("Detected python: %d.%d.%d" % (sys.version_info[0], sys.version_info[1], sys.version_info[2]))

if len(sys.argv) < 4:
    print("Not enough parameters. At least 3 are needed: filename.png sat_name aos")
    exit(-1)

filename=sys.argv[1]
sat_name=sys.argv[2]
aos=tca=los=sys.argv[3]
notes="..."

if len(sys.argv) >= 5:
    TCA = sys.argv[4]

if len(sys.argv) >= 6:
    LOS = sys.argv[5]

if len(sys.argv) >= 7:
    NOTES = sys.argv[6]

submit_observation(filename, sat_name, aos, tca, los, notes)

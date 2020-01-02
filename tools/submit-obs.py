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

# SSH connection
username="satnogs"

hostname="satnogs.klub.com.pl"
destdir="public_html/data"

# Uncomment this for local deployment
#hostname="localhost"
#destdir="/var/www/html"

# Postgres connection
dbuser="satnogs"
dbname="satnogs"

import sys
import os
import subprocess

def submit_observation(path, sat_name, aos, tca, los, notes):

    fnames = path.split("/")
    filename = fnames[-1]

    # First we need to make sure there's the destination directory
    params = []
    if hostname != "localhost":
        params.append("ssh")
        params.append(hostname)

    params.append("mkdir")
    params.append("-p")
    params.append(("%s/%s" % (destdir, "data")))
    subprocess.run(params)

    # Second step is to copy (cp or scp) the file to its destination
    params = []
    if hostname != "localhost":
        dst = "%s:%s/data" % (hostname, destdir)
        params.append("scp")
        print("Uploading file: cmd=[scp %s %s]" % (path, dst))
    else:
        dst = "%s/data" % destdir
        params.append("cp")
        print("Copying file locally: cp %s -> %s" % (path, dst))
    params.append(path)
    params.append(dst)

    # Commented out
    #subprocess.run(params)

    # Finally, we need to create the DB entry
    sqlcmd = "INSERT INTO observations(aos,sat_name,filename) VALUES('%s', '%s', '%s');" % (aos, sat_name, filename)
    print("Adding record in the db: sqlcmd=[%s]" % sqlcmd)

    params = []
    if hostname != "localhost":
        params.append("ssh")
        params.append(hostname)
        params.append("psql -c \"%s\" %s" % (sqlcmd, dbname))
    else:
        params.append("psql")
        params.append("-U")
        params.append(dbuser)
        params.append("-c")
        params.append(sqlcmd)
        params.append(dbname)
    subprocess.run(params)


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

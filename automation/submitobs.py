import os.path
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
hostname="localhost"
destdir="/var/www/html"

# Postgres connection
dbuser="satnogs"
dbname="satnogs"

import sys
import os
import subprocess

def submit_observation(image_path, sat_name, aos, tca, los, notes):

    directory, filename = os.path.split(image_path)

    # First we need to make sure there's the destination directory
    params = []
    if hostname != "localhost":
        params.append("ssh")
        params.append(hostname)

    params.append("mkdir")
    params.append("-p")
    params.append(("%s/data/thumbs" % (destdir, )))
    subprocess.call(params)

    # Make thumbnail
    thumbnail_path = os.path.join(directory, "thumb-" + filename)
    subprocess.call(["convert" ,"-thumbnail", "200", image_path, thumbnail_path])
    # Second step is to copy (cp or scp) the file to its destination
    for path, subdir in [(image_path, "data"), (thumbnail_path, "data/thumbs")]:
        params = []
        if hostname != "localhost":
            dst = "%s:%s/%s" % (hostname, destdir, subdir)
            params.append("scp")
        else:
            dst = "%s/data" % destdir
            params.append("cp")
        params.append(path)
        params.append(dst)

        subprocess.call(params)
    os.remove(thumbnail_path)

    # Finally, we need to create the DB entry
    sqlcmd = "INSERT INTO observations(aos,tca,los,sat_name,filename) VALUES('%s', '%s', '%s', '%s', '%s');" % (aos, tca, los, sat_name, filename)

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
    subprocess.call(params)


if __name__ == '__main__':
    if len(sys.argv) < 4:
        print("Not enough parameters. At least 3 are needed: filename.png sat_name aos")
        exit(1)

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

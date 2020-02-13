#!/usr/bin/python3

from subprocess import run
from os import listdir
from os.path import isfile, join

imgpath="/home/satnogs/data"
thumbpath="/home/satnogs/data/thumbs"

pngfiles = [f for f in listdir(imgpath) if isfile(join(imgpath, f)) and f.endswith(".png")]

for f in pngfiles:
    if f.startswith("thumb-"):
        continue
    if isfile(join(thumbpath, "thumb-" + f)):
        continue
    print("Generating thumbnail for %s" % f)
    run(["convert", "-thumbnail", "200", join(imgpath, f), join(thumbpath, "thumb-" + f)])

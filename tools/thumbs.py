#!/usr/bin/python3

from subprocess import run
from os import listdir
from os.path import isfile, join

imgpath="/home/satnogs/public_html/data"


pngfiles = [f for f in listdir(imgpath) if isfile(join(imgpath, f)) and f.endswith(".png")]

for f in pngfiles:
    if f.startswith("thumb-"):
        continue
    if isfile(join(imgpath, "thumb-" + f)):
        continue
    print("Generating thumbnail for %s" % f)
    run(["convert", "-thumbnail", "200", join(imgpath, f), join(imgpath, "thumb-" + f)])

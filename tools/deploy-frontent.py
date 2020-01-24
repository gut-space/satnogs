#!/usr/bin/python3

import os, errno
from shutil import copyfile

srcdir = "."
dstdir = "/home/satnogs/public_html"

docfiles = [
    "doc/satnogs-gdn-report.pdf",
    "slides/satnogs-gdn-overview.pdf",
    "poster/best/poster1-pl.jpg",
    "poster/best/poster2-en.jpg"
    ]

frontendfiles = [ "index.php" ]

# Try to create doc/ directory if it doesn't exist yet.
dstpath = os.path.join(dstdir, "doc")
try:
    os.makedirs(dstpath)
except:
    pass

for f in docfiles:
    src = os.path.join(srcdir, f)
    dst = os.path.join(dstdir, "doc", f[f.rfind("/")+1:])
    print("COPY %s => %s" % (src, dst))
    copyfile(src, dst)

for f in frontendfiles:
    src = os.path.join(srcdir, "frontend", f)
    dst = os.path.join(dstdir, f)
    print("COPY %s => %s" % (src, dst))
    copyfile(src, dst)

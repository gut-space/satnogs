#!/bin/bash

# This is a sample script that uploads observations to the frontend server.
# It must be run from the top level dir, e.g.
#
# captures/upload.sh
#

echo "UPLOAD 1"
python3 tools/submit-obs.py captures/2019-12-15-0854-noaa-18/20191215-0854-noaa-18.png noaa-18 "20191215 085453"

echo "UPLOAD 2"
python3 tools/submit-obs.py captures/2019-12-15-1947-noaa-18/gqrx_20191215_184701_137912500-telemetry_contrast.png NOAA-18 "2019-12-15 19:46:48"

echo "UPLOAD 3"
python3 tools/submit-obs.py captures/2019-12-16-1401-noaa-19/output-curves.png NOAA-19 "2019-12-16 14:59:20"

echo "UPLOAD 4"
python3 tools/submit-obs.py captures/2019-12-17-1829-noaa-18/output.png NOAA-18 "2019/12/17 18:23"

echo "UPLOAD 5"
python3 tools/submit-obs.py captures/2019-12-26-2059-noaa-18/output.png NOAA-18 "2019/12/26 20:59 UTC"

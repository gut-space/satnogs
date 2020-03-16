#!/bin/sh

# Recipe for receive NOAA APT transmissions

# Arguments
# 1: Prefix path. All path created by this script will be start with it
# 2: Freqency. Value can be specified as an integer (89100000), a float (89.1e6) or as a metric suffix (89.1M).
# 3: Recording duration in seconds

# Returns
# Print on stdout in format:
#	!! CATEGORY: PATH
# where CATEGORY is label, tag, category of file and PATH is path to this file.
# Caller is responsible for returned paths.

BASENAME=$1
FREQUENCY=$2
RECEIVE_TIMEOUT=$3

SIGNAL_FILENAME=${BASENAME}_signal.wav
PRODUCT_FILENAME=${BASENAME}_product.png

# Record signal
timeout $RECEIVE_TIMEOUT \
	rtl_fm -d 0 -f $FREQUENCY -s 48000 -g 49.6 -p 1 -F 9 -A fast -E DC - | \
	sox -t raw -b16 -es -r 48000 -c1 -V1 - $SIGNAL_FILENAME rate 11025

retVal=$?
if [ retVal -ne 0]; then
	exit $retVal
fi

echo !! Signal: $SIGNAL_FILENAME

# Decode signal
noaa-apt -o $PRODUCT_FILENAME $SIGNAL_FILENAME || exit $?
echo !! Product: $PRODUCT_FILENAME

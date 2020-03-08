#!/bin/sh

BASENAME=$1
FREQUENCY=$2
RECEIVE_TIMEOUT=$3

SIGNAL_FILENAME=${BASENAME}_signal.wav
PRODUCT_FILENAME=${BASENAME}_product.png

# Record signal
timeout $RECEIVE_TIMEOUT \
	rtl_fm -d 0 -f $FREQUENCY -s 48000 -g 49.6 -p 1 -F 9 -A fast -E DC - | \
	sox -t raw -b16 -es -r 48000 -c1 -V1 - $SIGNAL_FILENAME rate 11025

# Decode signal
noaa-apt -o $PRODUCT_FILENAME $SIGNAL_FILENAME

# Return result paths
echo !! Signal: $SIGNAL_FILENAME
echo !! Product: $PRODUCT_FILENAME

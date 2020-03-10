#!/bin/bash
# See: https://www.reddit.com/r/RTLSDR/comments/abn29d/automatic_meteor_m2_reception_on_linux_using_rtl/ed2teuv/
# Meteor-M 2 satellite reception

BASENAME=$1
FREQUENCY=$2
RECEIVE_TIMEOUT=$3

NON_NORMALIZED_SIGNAL_FILENAME=${BASENAME}_non_normalized_signal.wav
QPSK_FILENAME=${BASENAME}_qpsk.qpsk
DUMP_PREFIX_FILENAME=${BASENAME}_dump
PRODUCT_FILENAME_WITOUT_EXT=${BASENAME}_product
PRODUCT_BITMAP_FILENAME=${PRODUCT_FILENAME_WITOUT_EXT}.bmp

SIGNAL_FILENAME=${BASENAME}_signal.wav
PRODUCT_FILENAME=${PRODUCT_FILENAME_WITOUT_EXT}.png

# Record raw IQ data
timeout $RECEIVE_TIMEOUT \
    rtl_fm -M raw -f $FREQUENCY -s 288k -g 48 -p 1 | \
    sox -t raw -r 288k -c 2 -b 16 -e s - -t wav $NON_NORMALIZED_SIGNAL_FILENAME rate 96k

# Normalize .wav
sox $NON_NORMALIZED_SIGNAL_FILENAME $SIGNAL_FILENAME gain -n

# Demodulate .wav to QPSK
yes | meteor-demod -o $QPSK_FILENAME $SIGNAL_FILENAME

# Keep original file timestamp
touch -r $NON_NORMALIZED_SIGNAL_FILENAME $QPSK_FILENAME

# Decode QPSK
medet $QPSK_FILENAME ${DUMP_PREFIX_FILENAME} -cd

# Generate images
medet ${DUMP_PREFIX_FILENAME}.dec $PRODUCT_FILENAME_WITOUT_EXT -r 68 -g 65 -b 64 -d

# Convert to PNG
convert $PRODUCT_BITMAP_FILENAME $PRODUCT_FILENAME

rm $NON_NORMALIZED_SIGNAL_FILENAME
rm $QPSK_FILENAME
rm $PRODUCT_BITMAP_FILENAME
rm ${DUMP_PREFIX_FILENAME}*

echo !! Signal: $SIGNAL_FILENAME
echo !! Product: $PRODUCT_FILENAME

# Demodulator from: https://github.com/dbdexter-dev/meteor_demod
# Decoder from: https://github.com/artlav/meteor_decoder
# Mni Tnx to authors!

# timeout 600: reception time
# if your reception conditions are good, you can use "rate 120k" or more
# /something: replace with your path
# Works on RPi3
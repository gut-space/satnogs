import datetime
import logging
import sched
import subprocess

from orbit_predictor.sources import NoradTLESource
from orbit_predictor.locations import Location

import fakepredictor

scheduler = sched.scheduler()
logger = logging.getLogger(__name__)

HAS_SDR = False

# Prediction constants
NOAA_URL = r"https://celestrak.com/NORAD/elements/noaa.txt"
location = Location("Taneczna", 18, 52, 153)
SATELLITE = "NOAA 18"
AOS_AT_DG = 30
FREQUENCY = "137.9125e6"
BANDWIDTH = "2048000"

def get_now() -> datetime.datetime:
    return datetime.datetime.utcnow()

def get_predictor():
    if HAS_SDR:
        source = NoradTLESource.from_url(NOAA_URL)
        predictor = source.get_predictor(SATELLITE)
        return predictor
    else:
        return fakepredictor.FakePredictor(SATELLITE, 60)

def record(frequency: str, bandwidth: str, output_filename: str):
    '''
    rtl_sdr -f 137.620e6 -s 2048000 -g 29 -p 22 | sox -t raw -b 16 -e signed-integer -r 11025 -B -c1 NOAA15.wav
    '''

    if not HAS_SDR:
        print("Recording...", end="")
        return lambda: print("Stop recording!")

    rtl_process = subprocess.Popen(
        ["rtl_sdr", 
         "-f", frequency,
         "-s", bandwidth,
         "-g", 50,
         "-p", 22
        ], stdout=subprocess.PIPE
    )
    sox_process = subprocess.Popen(
        ["sox",
         "-t", "raw",
         "-b", 16,
         "-e", "signed-integer",
         "-r", 11025,
         "-B",
         "-c1",
         output_filename], stdin=rtl_process.stdout
    )

    terminate = lambda: rtl_process.terminate()
    return terminate

def on_stop_recording(terminate):
    terminate()
    logger.log(logging.DEBUG, "Stop recording")

def on_start_recording(los, frequency, bandwidth, output_filename):
    now = get_now()
    delay = los - now
    terminate = record(frequency, bandwidth, output_filename)
    logger.log(logging.DEBUG, "Recording on %s with bandwith %s to file %s" % (frequency, bandwidth, output_filename))
    scheduler.enter(delay.total_seconds(), 1, on_stop_recording, (terminate,))

def schedule_recording(frequency: str, bandwidth: str, output_filename: str, aos: datetime.datetime, los: datetime.datetime):    
    now = get_now()
    delay = aos - now
    scheduler.enter(delay.total_seconds(), 1, on_start_recording, (los, frequency, bandwidth, output_filename))

predictor = get_predictor()
next_pass = predictor.get_next_pass(location, aos_at_dg=AOS_AT_DG)

timestamp = next_pass.aos.strftime("%Y-%m-%d %H:%M:%S")
output_filename = "%s_%s_%s_%s.wav" % (SATELLITE, FREQUENCY, location.name, timestamp)

schedule_recording(FREQUENCY, BANDWIDTH, output_filename, next_pass.aos, next_pass.los)

scheduler.run()


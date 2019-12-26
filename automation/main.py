import datetime
import logging
import sched
import signal
import subprocess
import sys

from orbit_predictor.sources import NoradTLESource
from orbit_predictor.locations import Location

import fakepredictor

logging.basicConfig(level=logging.DEBUG, format='%(asctime)s %(levelname)s: %(message)s')
scheduler = sched.scheduler()

current_process_terminate = None

HAS_SDR = True

# Prediction constants
NOAA_URL = r"https://celestrak.com/NORAD/elements/noaa.txt"
location = Location("Taneczna", 54.3833, 18.4667, 138)
AOS_AT_DG = 0

frequencies = {
    "NOAA 15": "137.62e6",
    "NOAA 18": "137.9125e6",
    "NOAA 19": "137.1e6"
}

def sigint_handler(signal, frame):
    for event in scheduler.queue:
        scheduler.cancel(event)

    if current_process_terminate is not None:
        current_process_terminate()
    sys.exit(0)

signal.signal(signal.SIGINT, sigint_handler)

def get_now() -> datetime.datetime:
    return datetime.datetime.utcnow()

def record(frequency: str, output_filename: str):
    rtl_process = subprocess.Popen(
        ["rtl_fm", 
         "-d", "0",
         "-f", frequency,
         "-s", "48000",
         "-g", "49.6",
         "-p", "1",
         "-F", "9",
         "-A", "fast",
         "-E", "DC",
         "-"
        ], stdout=subprocess.PIPE
    )
    sox_process = subprocess.Popen(
        ["sox",
         "-t", "raw",
         "-b16",
         "-es",
         "-r", "48000",
         "-c1",
         "-V1",
         "-", 
         output_filename,
         "rate", "11025"], stdin=rtl_process.stdout
    )

    print(rtl_process.args)
    print(sox_process.args)

    terminate = lambda: rtl_process.terminate()
    current_process_terminate = terminate
    return terminate

def on_stop_recording(terminate):
    terminate()
    logging.debug("Stop recording")

def on_start_recording(los, frequency, output_filename):
    now = get_now()
    delay = los - now
    terminate = record(frequency, output_filename)
    logging.debug("Recording on %s to file %s" % (frequency, output_filename))
    scheduler.enter(delay.total_seconds(), 1, on_stop_recording, (terminate,))

def schedule_recording(frequency: str, satellite: str, aos: datetime.datetime, los: datetime.datetime):    
    timestamp = next_pass.aos.strftime("%Y-%m-%d %H:%M:%S")
    output_filename = "%s_%s_%s_%s.wav" % (satellite, frequency, location.name, timestamp)
    now = get_now()
    delay = aos - now
    logging.debug("Schedule recording %s from %s to %s" % (satellite, str(aos), str(los)))
    scheduler.enter(delay.total_seconds(), 1, on_start_recording, (los, frequency, output_filename))

def get_next_pass():
    source = NoradTLESource.from_url(NOAA_URL)
    next_pass = None
    next_sat = None
    for sat in ["NOAA 15", "NOAA 18", "NOAA 19"]:
        predictor = source.get_predictor(sat)
        pass_ = predictor.get_next_pass(location, aos_at_dg=AOS_AT_DG)
        logging.debug("%s - AOS: %s" %  (sat, str(pass_.aos)))
        if next_pass is None or pass_.aos < next_pass.aos:
            next_pass = pass_
            next_sat = sat

    return (next_sat, next_pass)

satellite, next_pass = get_next_pass()
frequency = frequencies[satellite]

schedule_recording(frequency, satellite, next_pass.aos, next_pass.los)

scheduler.run()


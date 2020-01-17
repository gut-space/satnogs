import datetime
import logging
import os
import signal
import subprocess
import sched
import sys
import typing

from utils import first, get_receiver_command, get_planner_command, open_config
from submitobs import submit_observation

RECEIVER_COMMAND = get_receiver_command()

current_process_terminate: typing.Callable = lambda: None

def sigint_handler(signal, frame):
    logging.debug("Terminate")
    if current_process_terminate is not None:
        current_process_terminate()
    sys.exit(0)

signal.signal(signal.SIGINT, sigint_handler)

def record(frequency: str, output_filename: str):
    logging.debug("Start recording")
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
    sox = subprocess.Popen(
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

    terminate = lambda: rtl_process.terminate()
    global current_process_terminate
    current_process_terminate = terminate
    return sox, terminate

def on_stop_recording(terminate):
    terminate()
    global current_process_terminate
    current_process_terminate = None
    logging.debug("Stop recording")

def decode_apt(input_path: str, output_path):
    process = subprocess.Popen([
        "noaa-apt",
        "-o", output_path,
        input_path
    ])
    process.wait()

config = open_config()

if __name__ == '__main__':
    _, name, los, *opts = sys.argv
    debug = len(opts) != 0

    satellite = first(config["satellites"], lambda s: s["name"] == name)
    if satellite is None:
        logging.error("Unknown satellite")
        sys.exit(1)

    now_datetime = datetime.datetime.utcnow()
    los_datetime = datetime.datetime.fromisoformat(los)
    delta = los_datetime - now_datetime

    wav_filename = "/tmp/%s_%s.wav" % (name, los)
    frequency = satellite["freq"]
    process, terminate = record(frequency, wav_filename)

    scheduler = sched.scheduler()
    scheduler.enter(delta.total_seconds(), 1, on_stop_recording, (terminate,))
    scheduler.run()
    process.wait()

    png_filename = "/tmp/%s_%s.png" % (name, los)
    decode_apt(wav_filename, png_filename)
    if not debug:
        os.remove(wav_filename)

    if not debug and os.path.exists(png_filename):
        submit_observation(png_filename, name, str(now_datetime), str(now_datetime), str(los_datetime), "")
        os.remove(png_filename)

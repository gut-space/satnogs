import datetime
import logging
import os
import signal
import subprocess
import sched
import shutil
import sys
import typing
from typing import Union, Optional

from utils import GLOBAL_SAVE_MODE, SATELLITE_SAVE_MODE, first, get_receiver_command, get_planner_command, open_config, SatelliteConfiguration
from submitobs import submit_observation
from postprocess import factory

RECEIVER_COMMAND = get_receiver_command()

current_process_terminate: Optional[typing.Callable] = lambda: None

def sigint_handler(signal, frame):
    logging.debug("Terminate")
    if current_process_terminate is not None:
        current_process_terminate()
    os.kill(os.getpid(), signal.SIGTERM)

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

def move_to_satellite_directory(root: str, sat_name: str, path: str):
    now = datetime.datetime.utcnow()
    timestamp_dir = now.strftime(r"%Y-%m-%d")
    base = os.path.basename(path)
    new_dir = os.path.join(root, sat_name, timestamp_dir)
    new_path = os.path.join(new_dir, base)

    os.makedirs(new_dir, exist_ok=True)
    shutil.move(path, new_path)

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

    # Post-processing
    save_mode: Optional[Union[SATELLITE_SAVE_MODE, GLOBAL_SAVE_MODE]]
    save_mode = satellite.get("save_to_disk", None)
    if save_mode is None or save_mode == "INHERIT":
        save_mode = config.get("save_to_disk", None)
    if save_mode is None:
        save_mode = "NONE"

    should_submit: Optional[bool]
    should_submit = satellite.get("submit", None)
    if should_submit is None:
        should_submit = config.get("submit", None)
    if should_submit is None:
        should_submit = True

    root_directory = config.get("obsdir")
    if root_directory is None:
        root_directory = "/tmp/observations"

    postprocess_path = factory.get_postprocess_result(name, wav_filename)

    if save_mode in ("SIGNAL", "ALL"):
        move_to_satellite_directory(root_directory, name, wav_filename)
    else:
        os.remove(wav_filename)

    if should_submit:
        submit_observation(postprocess_path, name, now_datetime, now_datetime, los_datetime, "")

    if save_mode in ("PRODUCT", "ALL"):
        move_to_satellite_directory(root_directory, name, postprocess_path)
    else:
        os.remove(postprocess_path)

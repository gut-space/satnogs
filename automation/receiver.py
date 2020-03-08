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

from utils import GLOBAL_SAVE_MODE, SATELLITE_SAVE_MODE, first, open_config, SatelliteConfiguration
from submitobs import submit_observation
from recipes import factory

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

    aos_datetime = datetime.datetime.utcnow()
    los_datetime = datetime.datetime.fromisoformat(los)

    results = factory.execute_recipe(satellite, los_datetime)

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

    signal = first(results, lambda r: r[0] == "signal")
    products = filter(lambda r: r[0] == "product", results)

    if save_mode in ("SIGNAL", "ALL") and signal is not None:
        move_to_satellite_directory(root_directory, name, signal[1])

    if should_submit:
        product = first(products, lambda _: True)
        if product is not None:
            submit_observation(product[1], name, aos_datetime, aos_datetime, los_datetime, "")

    if save_mode in ("PRODUCT", "ALL"):
        for _, path in products:
            move_to_satellite_directory(root_directory, name, path)

    for _, path in results:
        if os.path.exists(path):
            os.remove(path)

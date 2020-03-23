import datetime
import logging
import os
import shutil
import sys

from utils import first, open_config, get_satellite, from_iso_format
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

def cmd():
    _, name, los, *opts = sys.argv

    satellite = get_satellite(config, name)

    aos_datetime = datetime.datetime.utcnow()
    los_datetime = from_iso_format(los)

    results = factory.execute_recipe(satellite, los_datetime)

    # Post-processing
    save_mode = satellite["save_to_disk"]
    should_submit = satellite["submit"]

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

if __name__ == '__main__':
    try:
        cmd()
    except:
        _, name, los, *opts = sys.argv
        logging.error("Failed receive %s (LOS: %s)" % (name, los), exc_info=True)

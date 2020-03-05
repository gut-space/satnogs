#!/usr/bin/python
import datetime
import os
import requests
import sys
from typing import Any, Dict

from utils import open_config
from hmac_token import get_token, AUTHORIZATION_ALGORITHM

config = open_config()
section = config["server"]
station_id = str(section["id"])
secret = bytearray.fromhex(section["secret"])
url = section["url"]

def submit_observation(image_path: str, sat_name: str, aos: datetime.datetime, tca: datetime.datetime, los: datetime.datetime, notes: str):
    '''
    Submit observation to content server.

    Parameters
    ==========
    image_path: str
        Path to PNG image
    sat_name: str
        Satellite name compatible with NORAD format
    aos: datetime.datetime
        Acquisition of Signal (or Satellite)
    tca: datetime.datetime
        Time of Closest Approach
    los: datetime.datetime
        Loss of Signal (or Satellite)
    notes: str
        Any text note
    '''
    _, filename = os.path.split(image_path)
    form_data = {
        "aos": aos.isoformat(),
        "tca": tca.isoformat(),
        "los": los.isoformat(),
        "sat": sat_name,
        "notes": notes
    }

    file_obj = open(image_path, 'rb') 
    body: Dict[str, Any] = {
        "file": file_obj
    }
    body.update(form_data)

    token = get_token(station_id, secret, body, datetime.datetime.utcnow())

    headers = {
        "Authorization": "%s %s" % (AUTHORIZATION_ALGORITHM, token)
    }

    files = {
        "file": (
            filename,
            file_obj,
            "image/png",
            {}
        )
    }

    requests.post(url, form_data, headers=headers, files=files)

if __name__ == '__main__':
    if len(sys.argv) < 4:
        print("Not enough parameters. At least 3 are needed: filename.png sat_name aos")
        exit(1)

    filename=sys.argv[1]
    sat_name=sys.argv[2]
    aos=tca=los=datetime.datetime.fromisoformat(sys.argv[3])
    notes="..."

    if len(sys.argv) >= 5:
        TCA = sys.argv[4]

    if len(sys.argv) >= 6:
        LOS = sys.argv[5]

    if len(sys.argv) >= 7:
        NOTES = sys.argv[6]

    submit_observation(filename, sat_name, aos, tca, los, notes)

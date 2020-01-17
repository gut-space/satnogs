import datetime
import logging
import os
import requests
import time

from orbit_predictor.sources import NoradTLESource
from orbit_predictor.predictors.base import Predictor

from utils import DEV_ENVIRONEMT, CONFIG_DIRECTORY, first, APP_NAME

CELESTRAK = [
    r"https://celestrak.com/NORAD/elements/noaa.txt"
]

class OrbitDatabase:
    def __init__(self, urls=None, max_period=7*24*60*60):
        self.max_period = max_period
        if urls is None:
            urls = CELESTRAK
        self.urls = urls

    def _get_tle_from_url(self, url):
        headers = {'user-agent': APP_NAME, 'Accept': 'text/plain'}
        try:
            response = requests.get(url, headers=headers)
        except requests.exceptions.RequestException as error:
            logging.error("Exception requesting TLE: %s", error)
            raise
        return response.content.decode("UTF-8")

    def _get_current_tle_file(self, url: str):
        tle_filename = url[url.rindex("/") + 1:]
        tle_path = os.path.join(CONFIG_DIRECTORY, tle_filename)
        tle_path_exists = os.path.exists(tle_path)
        if tle_path_exists: 
            stat = os.stat(tle_path)
            ctime = stat.st_ctime
            now = time.time()
            if now < ctime + self.max_period:
                return tle_path

        try:
            content = self._get_tle_from_url(url)
            with open(tle_path, "w") as f:
                f.write(content)
            return tle_path
        except:
            if tle_path_exists:
                return tle_path
            else:
                raise

    def get_predictor(self, sat_id) -> Predictor:
        for url in self.urls:
            path = self._get_current_tle_file(url)
            source = NoradTLESource.from_file(path)
            try:
                source.get_tle(sat_id, datetime.datetime.utcnow())
                return source.get_predictor(sat_id)
            except LookupError:
                continue
        raise LookupError("Could not find %s in orbit data." % (sat_id,))
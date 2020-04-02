import datetime
import logging
import os
from typing import List, Sequence
import requests
import requests.exceptions
import time

from orbit_predictor.sources import NoradTLESource
from orbit_predictor.predictors.base import CartesianPredictor

from utils import CONFIG_DIRECTORY, APP_NAME, safe_filename, open_config

CELESTRAK = [
    r"https://celestrak.com/NORAD/elements/active.txt"
]

class OrbitDatabase:
    def __init__(self, urls=None, max_period=7*24*60*60):
        self.max_period = max_period
        if urls is None:
            config = open_config()
            urls = config['norad']
        if urls is None:
            urls = CELESTRAK
        self.urls: Sequence[str]
        self.urls = urls

    def _get_tle_from_url(self, url):
        headers = {'user-agent': APP_NAME, 'Accept': 'text/plain'}
        try:
            response = requests.get(url, headers=headers)
        except requests.exceptions.RequestException as error:
            logging.error("Exception requesting TLE: %s", error)
            raise
        return response.content.decode("UTF-8")

    def _fetch_tle_and_save(self, url, tle_path):
        content = self._get_tle_from_url(url)
        with open(tle_path, "w") as f:
            f.write(content)
        return tle_path

    def _get_tle_path_from_url(self, url):
        tle_filename = safe_filename(url)
        tle_path = os.path.join(CONFIG_DIRECTORY, tle_filename)
        return tle_path

    def _get_create_time(self, path):
        stat = os.stat(path)
        ctime = stat.st_ctime
        return ctime

    def _is_out_of_date(self, path):
        ctime = self._get_create_time(path)    
        now = time.time()
        return now > ctime + self.max_period

    def _get_current_tle_file(self, url: str, force_fetch=False):
        tle_path = self._get_tle_path_from_url(url)
        tle_path_exists = os.path.exists(tle_path)
        if not force_fetch and tle_path_exists and not self._is_out_of_date(tle_path):
            return tle_path

        try:
            return self._fetch_tle_and_save(url, tle_path)
        except:
            if not force_fetch and tle_path_exists:
                return tle_path
            else:
                raise

    def _is_in_source(self, source, sat_id):
        try:
            source.get_tle(sat_id, datetime.datetime.utcnow())
            return True
        except LookupError:
            return False

    def _get_source(self, sat_id):
        for url in self.urls:
            path = self._get_current_tle_file(url)
            source = NoradTLESource.from_file(path)
            if self._is_in_source(source, sat_id):
                return source
        raise LookupError("Could not find %s in orbit data." % (sat_id,))

    def get_predictor(self, sat_id: str) -> CartesianPredictor:
        source = self._get_source(sat_id)
        return source.get_predictor(sat_id)

    def get_tle(self, sat_id: str, date: datetime.datetime) -> List[str]:
        source = self._get_source(sat_id)
        return source.get_tle(sat_id, date).lines # type: ignore

    def refresh_satellites(self, sat_ids):
        all_sat_ids = set(sat_ids)
        found_sat_ids = set()
        for url in self.urls:
            satellites_to_search = all_sat_ids.difference(found_sat_ids)
            if len(satellites_to_search) == 0:
                return

            path = self._get_current_tle_file(url, force_fetch=True)
            source = NoradTLESource.from_file(path)
            
            for sat_id in satellites_to_search:
                if self._is_in_source(source, sat_id):
                    found_sat_ids.add(sat_id)        

        if all_sat_ids != found_sat_ids:
            raise LookupError("Could not find %s in orbit data." % (", ".join(all_sat_ids.difference(found_sat_ids))))
    
    def refresh_urls(self):
        urls = self.urls

        for url in urls:
            self._get_current_tle_file(url, force_fetch=True)

    def __str__(self):
        data = []
        for url in self.urls:
            path = self._get_tle_path_from_url(url)
            exists = os.path.exists(path)
            if exists:
                out_of_date = self._is_out_of_date(path)
                creation_time = self._get_create_time(path)
                now = time.time()
                age = now - creation_time
                
                dt = datetime.timedelta(seconds=age)
                data.append((url, "%s: %s ago" % ("Out-of-date" if out_of_date else "Current", str(dt))))
            else:
                data.append((url, "Not exists"))
        
        return "\n".join("%s - %s" % (url, desc) for url, desc in data)
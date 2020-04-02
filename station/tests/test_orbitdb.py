import datetime
from os import makedirs, environ
import os.path
import unittest
from shutil import copy, rmtree

# It must be set before import "utils"
environ["SATNOGS_GUT_CONFIG_DIR"] = "tests/config"

from utils import CONFIG_DIRECTORY

from orbitdb import OrbitDatabase

tle_filename = "https___celestrak.com_NORAD_elements_noaa.txt"

class TestOrbitDb(unittest.TestCase):
    def setUp(self):
        makedirs(CONFIG_DIRECTORY, exist_ok=True)
        copy("tests/config.yml", CONFIG_DIRECTORY)
        copy(os.path.join("tests", tle_filename),
            os.path.join(CONFIG_DIRECTORY, tle_filename))
        self.db = OrbitDatabase()

    def tearDown(self):
        rmtree(CONFIG_DIRECTORY, ignore_errors=True)

    def test_get_tle(self):
        now = datetime.datetime.utcnow()
        tle = self.db.get_tle("NOAA 15", now)
        
        self.assertIsNotNone(tle)
        self.assertEquals(len(tle), 2)
        tle_org = ("1 25338U 98030A   20093.30220133  .00000034  00000-0  32765-4 0  9993",
                   "2 25338  98.7251 118.7119 0011447 121.8181 238.4115 14.25957034138389")
        self.assertEqual(tle, tle_org)
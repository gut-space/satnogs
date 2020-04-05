import datetime
import os
import os.path
import shutil
import unittest
import logging
from logging import FileHandler

import testing.postgresql

from app import app
from app.hmac_token import get_authorization_header_value
from app.repository import Repository
from tests.utils import standard_seed_db, check_output

Postgresql: testing.postgresql.PostgresqlFactory

def setUpModule():
    global Postgresql
    Postgresql = testing.postgresql.PostgresqlFactory(cache_initialized_db=True,
                                                on_initialized=standard_seed_db)

def tearDownModule():
    # clear cached database at end of tests
    Postgresql.clear_cache()

IMAGE_ROOT = "tests/images"
LOG_FILE = "test.log"

class BasicTests(unittest.TestCase):

    def setUp(self):

        self.postgres = Postgresql()
        app.config['TESTING'] = True
        app.config['WTF_CSRF_ENABLED'] = False
        app.config['DEBUG'] = False
        app.config["database"] = self.postgres.dsn()
        app.config["storage"]["image_root"] = IMAGE_ROOT
        os.makedirs(os.path.join(IMAGE_ROOT, "thumbs"), exist_ok=True)
        self.app = app.test_client()

        # This is a test. Log EVERYTHING.
        logHandler = FileHandler(LOG_FILE)
        logHandler.setLevel(logging.DEBUG)
        app.logger.setLevel(logging.DEBUG)
        app.logger.addHandler(logHandler)

    def tearDown(self):
        self.postgres.stop()
        shutil.rmtree(IMAGE_ROOT, ignore_errors=True)
        os.remove(LOG_FILE)

    def test_main_page(self):
        response = self.app.get('/', follow_redirects=True)
        self.assertEqual(response.status_code, 200)
        # todo: check actual contents of the response

    def test_obslist(self):
        response = self.app.get('/obslist', follow_redirects=True)
        self.assertEqual(response.status_code, 200)

    def test_obs(self):
        response = self.app.get('/obs/750', follow_redirects=True)
        self.assertEqual(response.status_code, 200)

    def test_obs_missing(self):
        response = self.app.get('/obs/1', follow_redirects=True)
        self.assertEqual(response.status_code, 404)

    def test_obs_plots(self):
        response = self.app.get('/obs/751/az_el_polar.png', follow_redirects=True)
        self.assertEqual(response.status_code, 200)
        self.assertEqual(response.mimetype, 'image/png')
        response = self.app.get('/obs/751/az_el_by_time.png', follow_redirects=True)
        self.assertEqual(response.status_code, 200)
        self.assertEqual(response.mimetype, 'image/png')

    def test_obs_plots_missing(self):
        response = self.app.get('/obs/750/az_el_polar.png', follow_redirects=True)
        self.assertEqual(response.status_code, 404)
        response = self.app.get('/obs/750/az_el_by_time.png', follow_redirects=True)
        self.assertEqual(response.status_code, 404)

    def test_stations(self):
        response = self.app.get('/stations', follow_redirects=True)
        self.assertEqual(response.status_code, 200)

    def test_station(self):
        response = self.app.get('/station/1', follow_redirects=True)
        self.assertEqual(response.status_code, 200)

    def test_receive_obs(self):
        repository = Repository()
        station_id = 1
        secret = repository.read_station_secret(station_id)

        data = {
            'aos': datetime.datetime(2020, 3, 28, 12, 00),
            'tca': datetime.datetime(2020, 3, 28, 12, 15),
            'los': datetime.datetime(2020, 3, 28, 12, 30),
            'sat': 'NOAA 15',
            'notes': 'note text',
            "file0": open("tests/x.png", 'rb'),
            "file1": open("tests/x.png", 'rb'),
            "tle": [
                # Include trailling character
                "1 25544U 98067A   08264.51782528 -.00002182  00000-0 -11606-4 0  2927 ",
                "2 25544  51.6416 247.4627 0006703 130.5360 325.0288 15.72125391563537"
            ]
        }

        header_value = get_authorization_header_value(str(station_id), secret,
            data)
        headers = {
            'Authorization': header_value
        }
        response = self.app.post('/receive', data=data, headers=headers)
        self.assertEqual(response.status_code, 204)
        file_count = lambda dir_: len(
            [f for f in os.listdir(dir_)
                if os.path.isfile(os.path.join(dir_, f))]
        )
        self.assertEqual(file_count(IMAGE_ROOT), 2)
        self.assertEqual(file_count(os.path.join(IMAGE_ROOT, "thumbs")), 1)

        # Todo: Need to check if the DB entries have been added.

        # Check if there are appropriate entries in the log file.
        self.check_log(["0-tests_x.png written to tests/images",
                        "1-tests_x.png written to tests/images"])

    def check_log(self, strings):
        """Checks if there are specific strings present in the log file"""

        # Check that the log is there
        self.assertTrue(os.path.isfile(LOG_FILE))
        with open(LOG_FILE, 'r') as l:
            log = l.read()
            check_output(self, log, strings)

    def test_receive_obs_error(self):
        """Test error handling in the receive routine."""

        repository = Repository()
        station_id = 1

        # Check what happens if the path is misconfigured (or the server is not able to write file)
        self.app.root = app.config["storage"]['image_root'] = '/nonexistent/path'
        secret = repository.read_station_secret(station_id)

        data = {
            'aos': datetime.datetime(2020, 3, 28, 12, 00),
            'tca': datetime.datetime(2020, 3, 28, 12, 15),
            'los': datetime.datetime(2020, 3, 28, 12, 30),
            'sat': 'NOAA 15',
             # 'notes': optional,
            "file0": open("tests/x.png", 'rb'),
            "file1": open("tests/x.png", 'rb')
        }

        header_value = get_authorization_header_value(str(station_id), secret,
            data)
        headers = {
            'Authorization': header_value
        }
        response = self.app.post('/receive', data=data, headers=headers)


        self.assertEqual(response.status_code, 503)

        # Check if there's appropriate entry in the log file.
        self.check_log(["Failed to write /nonexistent/path/", "tests_x.png (image_root=/nonexistent/path)"])

if __name__ == "__main__":
    unittest.main()

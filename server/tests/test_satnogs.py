import datetime
import os
import shutil
import unittest

import testing.postgresql

from app import app
from app.hmac_token import get_authorization_header_value
from app.repository import Repository
from tests.utils import standard_seed_db

Postgresql: testing.postgresql.PostgresqlFactory

def setUpModule():
    global Postgresql
    Postgresql = testing.postgresql.PostgresqlFactory(cache_initialized_db=True,
                                                on_initialized=standard_seed_db)

def tearDownModule():
    # clear cached database at end of tests
    Postgresql.clear_cache()

IMAGE_ROOT = "tests/images"

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

    def tearDown(self):
        self.postgres.stop()
        shutil.rmtree(IMAGE_ROOT, ignore_errors=True)

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
            'notes': None,
            "file0": open("tests/x.png", 'rb'),
            "file1": open("tests/x.png", 'rb')
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

if __name__ == "__main__":
    unittest.main()

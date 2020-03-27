import unittest

import testing.postgresql

from app import app
from tests.utils import standard_seed_db

Postgresql = testing.postgresql.PostgresqlFactory(cache_initialized_db=True,
                                                  on_initialized=standard_seed_db)

def tearDownModule():
    # clear cached database at end of tests
    Postgresql.clear_cache()

class BasicTests(unittest.TestCase):

    def setUp(self):
        self.postgres = Postgresql()
        app.config['TESTING'] = True
        app.config['WTF_CSRF_ENABLED'] = False
        app.config['DEBUG'] = False
        app.config["database"] = self.postgres.dsn()
        self.app = app.test_client()

    def tearDown(self):
        self.postgres.stop()

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

if __name__ == "__main__":
    unittest.main()

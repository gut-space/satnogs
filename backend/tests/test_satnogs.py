import unittest

from app import app

class BasicTests(unittest.TestCase):

    ############################
    #### setup and teardown ####
    ############################

    # executed prior to each test
    def setUp(self):
        app.config['TESTING'] = True
        app.config['WTF_CSRF_ENABLED'] = False
        app.config['DEBUG'] = False
        self.app = app.test_client()
        #db.drop_all()
        #db.create_all()


    # executed after each test
    def tearDown(self):
        pass


###############
#### tests ####
###############

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

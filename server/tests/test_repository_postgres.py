import datetime
import os
import unittest
from functools import wraps

import testing.postgresql

from tests.utils import standard_seed_db
from app.repository import Observation, ObservationFile, ObservationFileId, ObservationId, Repository, SatelliteId, StationId

Postgresql: testing.postgresql.PostgresqlFactory

def setUpModule():
    global Postgresql
    Postgresql = testing.postgresql.PostgresqlFactory(cache_initialized_db=True,
                                                  on_initialized=standard_seed_db)

def tearDownModule():
    # clear cached database at end of tests
    Postgresql.clear_cache()

def use_repository(f):
    @wraps(f)
    def wrapper(self, *args, **kwargs):
        config = self.db_config
        repository = Repository(config)
        return f(self, repository, *args, **kwargs)
    return wrapper

class RepositoryPostgresTests(unittest.TestCase):

    def setUp(self):
        self.postgres = Postgresql()

    def tearDown(self):
        self.postgres.stop()

    @property
    def db_config(self):
        return self.postgres.dsn()

    @use_repository
    def test_db_version(self, repository):
        """Check if DB version is reported properly."""
        directory = "db"

        # List the schema upgrades script, get the highest number.
        migration_numbers = []
        for filename in os.listdir(directory):
            base, _ = os.path.splitext(filename)
            _, number_raw = base.split('-')
            number = int(number_raw)
            migration_numbers.append(number)
        version_from_filename = max(migration_numbers)

        # Get the DB version from the DB, check that it matches the one from migration scripts.
        version = repository.get_database_version()
        self.assertEqual(version, version_from_filename)

    @use_repository
    def test_read_observations(self, repository: Repository):
        """Check if a list of observations is returned properly."""
        obslist = repository.read_observations()

        # Make sure there are at least 3 observations (more may be added in the future.
        # This test should be future-proof.)
        self.assertGreaterEqual(len(obslist), 3)

        # Check if the data returned matches values from tests/db-data.psql
        assert(obslist[-3]['obs_id'] == 752)
        assert(obslist[-2]['obs_id'] == 751)
        assert(obslist[-1]['obs_id'] == 750)

        assert(obslist[-3]['aos'] == datetime.datetime(2020, 3, 8, 17, 24, 2, 88677))
        assert(obslist[-3]['tca'] == datetime.datetime(2020, 3, 8, 17, 34, 56, 789012))
        assert(obslist[-3]['los'] == datetime.datetime(2020, 3, 8, 17, 39, 6, 960326))
        assert(obslist[-3]['sat_id'] == 28654)
        assert(obslist[-3]['thumbnail'] == "thumb-f6b927bf-1472-4ea6-8657-48265cfae5ca-NOAA 18_2020-03-08T17:39:06.960326_apt.png")
        assert(obslist[-3]['station_id'] == 1)
        assert(obslist[-3]['notes'] == None)

        assert(obslist[-2]['aos'] == datetime.datetime(2020, 3, 8, 16, 17, 2, 639337))
        assert(obslist[-2]['tca'] == datetime.datetime(2020, 3, 8, 16, 17, 25, 567890))
        assert(obslist[-2]['los'] == datetime.datetime(2020, 3, 8, 16, 32, 56, 166600))
        assert(obslist[-2]['sat_id'] == 25338)
        assert(obslist[-2]['thumbnail'] == "thumb-72e94349-19ad-428c-b812-526971705607-NOAA 15_2020-03-08T16:32:56.166600_apt.png")
        assert(obslist[-2]['station_id'] == 1)
        assert(obslist[-2]['notes'] == None)

        assert(obslist[-1]['aos'] == datetime.datetime(2020, 3, 8, 15, 35, 2, 42786))
        assert(obslist[-1]['tca'] == datetime.datetime(2020, 3, 8, 15, 40, 1, 234567))
        assert(obslist[-1]['los'] == datetime.datetime(2020, 3, 8, 15, 51, 33, 972692))
        assert(obslist[-1]['sat_id'] == 33591)
        assert(obslist[-1]['thumbnail'] == "thumb-eb38486b-cd40-4879-81e9-31131766e84b-NOAA 19_2020-03-08T15:51:33.972692_apt.png")
        assert(obslist[-1]['station_id'] == 1)
        assert(obslist[-1]['notes'] == None)

    @use_repository
    def test_read_observation(self, repository: Repository):
        obs = repository.read_observation(750)

        # Now check if the response is as expected.
        self.assertTrue(obs)
        self.assertEqual(obs['obs_id'], 750)
        assert(obs['aos'] == datetime.datetime(2020, 3, 8, 15, 35, 2, 42786))
        assert(obs['tca'] == datetime.datetime(2020, 3, 8, 15, 40, 1, 234567))
        assert(obs['los'] == datetime.datetime(2020, 3, 8, 15, 51, 33, 972692))
        assert(obs['sat_id'] == 33591)
        assert(obs['thumbnail'] == "thumb-eb38486b-cd40-4879-81e9-31131766e84b-NOAA 19_2020-03-08T15:51:33.972692_apt.png")
        assert(obs['station_id'] == 1)
        assert(obs['notes'] == None)

    @use_repository
    def test_read_observation_invalid(self, repository: Repository):
        obs = repository.read_observation(12345) # no such observation
        assert obs == None

    @use_repository
    def test_observation_cr_d(self, repository: Repository):
        """Test checks if Create, Retrieve and Delete operations work for observations."""
        observation: Observation = {
            'obs_id': ObservationId(0),
            'aos': datetime.datetime(2020, 3, 21, 12, 00, 0),
            'tca': datetime.datetime(2020, 3, 21, 12, 15, 0),
            'los': datetime.datetime(2020, 3, 21, 12, 30, 0),
            'sat_id': SatelliteId(1),
            'thumbnail': 'thumb-123.png',
            'notes': None,
            'station_id': StationId(1)
        }

        obs_id = repository.insert_observation(observation)
        self.assertEqual(type(obs_id), int)

        observation_file: ObservationFile = {
            'obs_file_id': ObservationFileId(0),
            'filename': '123.png',
            'media_type': 'image/png',
            'obs_id': obs_id
        }

        file_id = repository.insert_observation_file(observation_file)
        self.assertEqual(type(file_id), int)

        observation_files = repository.read_observation_files(obs_id)
        self.assertEqual(len(observation_files), 1)

        observation_file["obs_file_id"] = file_id
        db_observation_file = observation_files[0]
        self.assertDictEqual(observation_file, db_observation_file) # type: ignore

        repository.delete_observation(obs_id)

        observation_files = repository.read_observation_files(obs_id)
        self.assertEqual(len(observation_files), 0)
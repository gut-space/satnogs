import datetime
import os
import unittest
from functools import wraps

import testing.postgresql

from tests.utils import standard_seed_db
from app.repository import (Observation, ObservationFile, ObservationFileId, ObservationId, Repository, SatelliteId, StationId,
    Station, Observation)

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

    def check_obs750(self, obs: Observation):
        """Check if returned parameters match observation 750 defined in tests/db-data.psql"""
        self.assertIsNotNone(obs)
        assert(obs['obs_id'] == 750)
        assert(obs['aos'] == datetime.datetime(2020, 3, 8, 15, 35, 2, 42786))
        assert(obs['tca'] == datetime.datetime(2020, 3, 8, 15, 40, 1, 234567))
        assert(obs['los'] == datetime.datetime(2020, 3, 8, 15, 51, 33, 972692))
        assert(obs['sat_id'] == 33591)
        assert(obs['thumbnail'] == "thumb-eb38486b-cd40-4879-81e9-31131766e84b-NOAA 19_2020-03-08T15:51:33.972692_apt.png")
        assert(obs['station_id'] == 1)
        assert(obs['notes'] == None)

    def check_obs751(self, obs: Observation):
        """Check if returned parameters match observation 751 defined in tests/db-data.psql"""
        self.assertIsNotNone(obs)
        assert(obs['obs_id'] == 751)
        assert(obs['aos'] == datetime.datetime(2020, 3, 8, 16, 17, 2, 639337))
        assert(obs['tca'] == datetime.datetime(2020, 3, 8, 16, 17, 25, 567890))
        assert(obs['los'] == datetime.datetime(2020, 3, 8, 16, 32, 56, 166600))
        assert(obs['sat_id'] == 25338)
        assert(obs['thumbnail'] == "thumb-72e94349-19ad-428c-b812-526971705607-NOAA 15_2020-03-08T16:32:56.166600_apt.png")
        assert(obs['station_id'] == 1)
        assert(obs['notes'] == None)

    def check_obs752(self, obs: Observation):
        """Check if returned parameters match observation 752 defined in tests/db-data.psql"""
        self.assertIsNotNone(obs)
        assert(obs['obs_id'] == 752)
        assert(obs['aos'] == datetime.datetime(2020, 3, 8, 17, 24, 2, 88677))
        assert(obs['tca'] == datetime.datetime(2020, 3, 8, 17, 34, 56, 789012))
        assert(obs['los'] == datetime.datetime(2020, 3, 8, 17, 39, 6, 960326))
        assert(obs['sat_id'] == 28654)
        assert(obs['thumbnail'] == "thumb-f6b927bf-1472-4ea6-8657-48265cfae5ca-NOAA 18_2020-03-08T17:39:06.960326_apt.png")
        assert(obs['station_id'] == 1)
        assert(obs['notes'] == None)

    @use_repository
    def test_read_observations(self, repository: Repository):
        """Check if a list of observations is returned properly."""
        obslist = repository.read_observations()

        # Make sure there are at least 3 observations (more may be added in the future.
        # This test should be future-proof.)
        self.assertGreaterEqual(len(obslist), 3)

        # Check if the data returned matches values from tests/db-data.psql
        self.check_obs750(obslist[-1])
        self.check_obs751(obslist[-2])
        self.check_obs752(obslist[-3])

    @use_repository
    def test_read_observation(self, repository: Repository):
        obs = repository.read_observation(750)

        # Now check if the response is as expected.
        self.check_obs750(obs)

        # Now test negative case. There's nos uch observation
        obs = repository.read_observation(12345)
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

    def check_station1(self, s: Station):
        """Check if returned parameters match station-id=1 defined in tests/db-data.psql"""
        self.assertEqual(s[0]['station_id'], 1)
        self.assertEqual(s[0]['name'], 'TKiS-1')
        self.assertEqual(s[0]['lon'], 18.531787)
        self.assertEqual(s[0]['lat'], 54.352469)
        self.assertEqual(s[0]['config'], 'WiMo TA-1 antenna (omni), RTL-SDR v3, Raspberry Pi 4B')
        self.assertEqual(s[0]['registered'], datetime.datetime(2019, 12, 15, 8, 54, 53))
        self.assertEqual(s[1], 3) # Number of observations
        self.assertEqual(s[2], datetime.datetime(2020, 3, 8, 17, 39, 6, 960326)) # Last observation.

    def check_station2(self, s: Station):
        """Check if returned parameters match station-id=2 defined in tests/db-data.psql"""
        self.assertEqual(s[0]['station_id'], 2)
        self.assertEqual(s[0]['name'], 'ETI-1')
        self.assertEqual(s[0]['lon'], 18.613253)
        self.assertEqual(s[0]['lat'], 54.37089)
        self.assertEqual(s[0]['descr'], 'Planned ground station at ETI faculty of Gdansk University of Technology')
        self.assertEqual(s[0]['config'], 'Configuration is TBD')
        self.assertEqual(s[0]['registered'], datetime.datetime(2020, 2, 16, 21, 15, 20, 615274))
        self.assertEqual(s[1], 0) # Number of observations
        self.assertEqual(s[2], None) # Last observation.

    @use_repository
    def test_stations(self, repository: Repository):
        gslist = repository.read_stations()
        self.assertGreaterEqual(len(gslist), 2)
        s1, s2 = gslist

        self.check_station1(s1)
        self.check_station2(s2)

        # Now limit number of returned stations to just one. There should be only station-id 1.
        gslist = repository.read_stations(limit=1)
        self.assertEqual(len(gslist), 1)
        self.check_station1(gslist[0]) # This should return values for station-id 1

        # Now skip the first station. Only station 2 should be returned.
        gslist = repository.read_stations(offset=1)
        self.assertEqual(len(gslist), 1)
        self.check_station2(gslist[0]) # This should return values for station-id 2

    @use_repository
    def test_station(self, repository: Repository):
        station = repository.read_station(1)
        self.assertIsNotNone(station)
        self.check_station1(station)

        # Now check invalid case. There's no such station
        station = repository.read_station(123)
        self.assertIsNone(station)

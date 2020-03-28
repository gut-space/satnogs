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
        directory = "db"
        
        migration_numbers = []
        for filename in os.listdir(directory):
            base, _ = os.path.splitext(filename)
            _, number_raw = base.split('-')
            number = int(number_raw)
            migration_numbers.append(number)
        version_from_filename = max(migration_numbers)

        version = repository.get_database_version()
        self.assertEqual(version, version_from_filename)

    @use_repository
    def test_read_observations(self, repository: Repository):
        observations = repository.read_observations()
        self.assertNotEqual(len(observations), 0)

    @use_repository
    def test_observation_cr_d(self, repository: Repository):
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
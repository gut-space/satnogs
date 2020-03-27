import unittest
from unittest import mock

from app.repository import Repository

class RepositoryTests(unittest.TestCase):

    @mock.patch("psycopg2.connect")
    def test_db_version(self, mock_connect):
        repostory = Repository({})
        mock_cursor = mock_connect.return_value.cursor.return_value
        mock_cursor.fetchone.side_effect =  [{"count": 1}, (3,), {"version": 15}]

        version = repostory.get_database_version()
        self.assertEqual(version, 15)
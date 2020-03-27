'''
Module encapsulate database operations.
It is responsible for create and execute SQL queries and support transactional.
'''

from configparser import Error
from datetime import datetime
from functools import wraps
from typing import Any, Dict, List, NewType, Sequence, NoReturn, Union, Optional, Tuple
import sys

if sys.version_info >= (3, 8):
    from typing import TypedDict, Literal
else:
    from typing_extensions import TypedDict, Literal

import psycopg2
from psycopg2.extras import RealDictCursor

# Data model

ObservationId = NewType("ObservationId", int)
ObservationFileId = NewType("ObservationFileId", int)
StationId = NewType("StationId", int)
SatelliteId = NewType("SatelliteId", int)
StationPhotoId = NewType("StationPhotoId", int)

class ObservationFile(TypedDict):
    obs_file_id: ObservationFileId
    filename: str
    media_type: str
    obs_id: ObservationId

class Observation(TypedDict):
    obs_id: ObservationId
    aos: datetime
    tca: datetime
    los: datetime
    sat_id: SatelliteId
    thumbnail: str
    notes: Optional[str]
    station_id: StationId

class Satellite(TypedDict):
    sat_id: SatelliteId
    sat_name: str

class Station(TypedDict):
    station_id: StationId
    name: str
    lon: float
    lat: float
    descr: str
    config: str
    registered: datetime

class StationPhoto(TypedDict):
    photo_id: StationPhotoId
    station_id: StationId
    sort: int
    filename: str
    descr: str

# Utils
def without_keys(d, keys: Sequence[str]):
    return {x: d[x] for x in d if x not in keys}

def exclude_from_dict(d, keys: Sequence[str]):
    excluded = [d[k] for k in keys]
    return without_keys(d, keys), *excluded

# Errors
class RepositoryError(Exception):
    '''Base class for Repository module errors.'''
    def __init__(self, message: str):
        super().__init__(message)

class TransactionAlreadyOpenError(RepositoryError):
    def __init__(self):
        super().__init__("Other transaction is already open on this repository. " \
                        "You may to have only one transaction opened in the same time")

# Psycopg2 doesn't provide typing in current version.
Connection = Any
Cursor = RealDictCursor

class _TransactionContext(TypedDict):
    conn: Connection
    cursor: Cursor

def use_cursor(f):
    '''
    Decorator who ensures that connection is establish and has created cursor.

    If no transaction is pending then it will be create before execution and commit
    (if execution not throw exceptions) and close after.

    If transaction is pending then it will be used, but not commit after execution.

    You need use this decorator before any public method (endpoint) in repository
    if it uses database connection.
    '''
    @wraps(f)
    def wrapper(*args, **kwargs):
        self_obj: Repository = args[0]

        if self_obj.is_pending_transaction:
            res = f(*args, **kwargs)
        else:
            with self_obj.transaction() as t:
                res = f(*args, **kwargs)
                t.commit()

        return res

    return wrapper

class Repository:
    '''
    Class for communication with database.

    You can use it with or without transactional.
    If you don't open transaction manually then it will
    be create, commit and close automatically.

    For transactional use .transaction method with context manager.
    '''
    def __init__(self, config=None):
        '''
        Config is dictionary of psycopg2.connect method. If you don't
        provide it then data from INI will be used.
        '''
        if config is None:
            from app import app
            config = app.config["database"]
        self._config = config
        self._transaction_context: Optional[_TransactionContext] = None # type: ignore

    @property
    def is_pending_transaction(self):
        return self._transaction_context is not None

    @property
    def _cursor(self) -> Cursor:
        '''Return Cursor in curret transacion.'''
        context = self._transaction_context
        return context.get("cursor")

    @use_cursor
    def read_observations(self, limit:int=100, offset:int=0) -> Sequence[Observation]:
        q = ("SELECT obs_id, aos, tca, los, "
                    "sat_id, "
                    "thumbnail, " 
                    "station_id, notes "
            "FROM observations "
            "ORDER BY aos DESC "
            "LIMIT %s OFFSET %s")
        cursor = self._cursor
        cursor.execute(q, (limit, offset))
        return cursor.fetchall()
        
    @use_cursor
    def read_observation(self, obs_id: ObservationId) -> Optional[Observation]:
        q = ("SELECT obs_id, aos, "
                "tca, los, "
                "thumbnail, "
                "station_id, notes "
            "FROM observations "
            "WHERE obs_id = %s"
            "ORDER BY aos DESC "
            "LIMIT 1")
        cursor = self._cursor
        cursor.execute(q, (obs_id,))
        return cursor.fetchone()
    
    @use_cursor
    def insert_observation(self, observation: Observation) -> ObservationId:
        cursor = self._cursor
        cursor.execute(
            "INSERT INTO observations (aos, tca, los, sat_id, thumbnail, notes, station_id) "
            "VALUES (%(aos)s, %(tca)s, %(los)s, %(sat_id)s, %(thumbnail)s, %(notes)s, %(station_id)s) "
            "RETURNING obs_id;",
            {
                'aos': observation["aos"].isoformat(),
                'tca': observation['tca'].isoformat(),
                'los': observation['los'].isoformat(),
                'sat_id': observation['sat_id'],
                'thumbnail': observation['thumbnail'],
                'notes': observation['notes'],
                'station_id': observation['station_id']
            }
        )
        return cursor.fetchone()['obs_id']

    @use_cursor
    def delete_observation(self, obs_id: ObservationId):
        q = ("DELETE "
             "FROM observations "
             "WHERE obs_id = %s;")
        cursor = self._cursor
        cursor.execute(q, (obs_id,))

    @use_cursor
    def read_observation_files(self, obs_id: ObservationId) -> Sequence[ObservationFile]:
        q = ("SELECT obs_file_id, filename, media_type, obs_id "
            "FROM observation_files "
            "WHERE obs_id = %s")
        cursor = self._cursor
        cursor.execute(q, (obs_id,))
        return cursor.fetchall()

    @use_cursor
    def insert_observation_file(self, observation_file: ObservationFile) -> ObservationFileId:
        q = ("INSERT INTO observation_files "
                "(filename, media_type, obs_id) "
             "VALUES "
                "(%(filename)s, %(media)s, %(obs)s) "
             "RETURNING obs_file_id;")
        cursor = self._cursor
        cursor.execute(q, {
            'filename': observation_file['filename'],
            'media': observation_file['media_type'],
            'obs': observation_file['obs_id']
        })
        return cursor.fetchone()['obs_file_id']


    @use_cursor
    def read_satellite(self, sat: Union[SatelliteId, str]) -> Optional[Satellite]:
        if type(sat) == str:
            q = "SELECT sat_id, sat_name FROM satellites WHERE sat_name = %s LIMIT 1;"
        else:
            q = "SELECT sat_id, sat_name FROM satellites WHERE sat_id = %s LIMIT 1;"
        cursor = self._cursor
        cursor.execute(q, (sat,))
        return cursor.fetchone()

    @use_cursor
    def read_stations(self, limit=100, offset=0) -> Sequence[Tuple[Station, int, datetime]]:
        q = ("SELECT s.station_id, s.name, s.lon, s.lat, s.descr, s.config, s.registered, "
                    "COUNT(o) AS count, MAX(o.los) AS los "
            "FROM stations s "
            "LEFT JOIN observations o ON s.station_id = o.station_id "
            "GROUP BY s.station_id "
            "LIMIT %s OFFSET %s")

        cursor = self._cursor
        cursor.execute(q, (limit, offset))
        items = cursor.fetchall()
        return [exclude_from_dict(i, ("count", "los")) for i in items]

    @use_cursor
    def read_station(self, id_: StationId) -> Optional[Tuple[Station, int, datetime]]:
        q = ("SELECT s.station_id, s.name, s.lon, s.lat, s.descr, s.config, s.registered, "
                    "COUNT(o) AS count, MAX(o.los) AS los "
            "FROM stations s "
            "LEFT JOIN observations o ON s.station_id = o.station_id "
            "WHERE s.station_id = %s "
            "GROUP BY s.station_id "
            "LIMIT 1")

        cursor = self._cursor
        cursor.execute(q, (id_,))
        row = cursor.fetchone()
        if row is None:
            return None

        count: int
        lastobs: datetime
        count, lastobs = row["count"], row["los"]
        del row["count"]
        del row["los"]
        return row, count, lastobs

    @use_cursor
    def read_station_photos(self, id_: StationId) -> Sequence[StationPhoto]:
        q = ("SELECT photo_id, station_id, sort, filename, descr "
            "FROM station_photos "
            "WHERE station_id = %s")

        cursor = self._cursor
        cursor.execute(q, (id_,))
        return cursor.fetchall()

    @use_cursor
    def read_station_secret(self, station_id: StationId) -> Optional[bytes]:
        query = "SELECT secret FROM stations WHERE station_id = %s"
        cursor = self._cursor
        cursor.execute(query, (station_id,))
        row = cursor.fetchone()
        if row is None:
            return None
        return row["secret"]

    @use_cursor
    def get_database_version(self) -> int:
        '''
        Returns database version. Return 0 if database is empty.
        @see: https://stackoverflow.com/a/42693458
        '''
        is_database_empty_query = ("SELECT count(*) AS count "
                "FROM pg_class c "
                "JOIN pg_namespace s ON s.oid = c.relnamespace "
                "WHERE s.nspname NOT IN ('pg_catalog', 'information_schema') "
                        "AND s.nspname NOT LIKE 'pg_temp%' "
                        "AND s.nspname <> 'pg_toast'")

        cursor = self._cursor
        cursor.execute(is_database_empty_query)
        is_database_empty = cursor.fetchone()["count"] == 0
        
        if is_database_empty:
            return 0

        exists_query = ("SELECT EXISTS ( "
                        "SELECT FROM information_schema.tables "
                        "WHERE table_schema = 'public' "
                            "AND  table_name = 'schema' "
                        ");")
        cursor.execute(exists_query)
        res = cursor.fetchone()
        is_table_version_exists = len(res) == 1
        if not is_table_version_exists:
            return 1

        version_query = 'SELECT "version" FROM "schema" LIMIT 1'
        cursor.execute(version_query)
        row = cursor.fetchone()
        if row is None:
            raise Exception("Database version not set")
        return row["version"]

    @use_cursor
    def execute_raw_query(self, query):
        cursor = self._cursor
        cursor.execute(query)

    def transaction(self):
        '''Create new transaction.'''
        return Transaction(self)

    
        
class Transaction:
    def __init__(self, repository: Repository):
        self._repository = repository

    @property
    def _transaction_context(self) -> Optional[_TransactionContext]:
        '''Retrive context from repository'''
        repository = self._repository
        return repository._transaction_context

    @_transaction_context.setter
    def _transaction_context(self, transaction_context: Optional[_TransactionContext]):
        '''Set new context in repository'''
        self._repository._transaction_context = transaction_context

    def commit(self):
        '''Save changes permanently'''
        context = self._transaction_context
        conn = context["conn"]
        conn.commit()

    def rollback(self):
        '''Revert changes'''
        context = self._transaction_context
        conn = context["conn"]
        conn.rollback()

    def __enter__(self):
        '''Open new connection and cursor. Store them in repository.'''
        if self._transaction_context is not None:
            raise TransactionAlreadyOpenError()

        config = self._repository._config
        conn: Connection = psycopg2.connect(**config)
        cursor: Cursor = conn.cursor(cursor_factory=RealDictCursor)
        transaction_context: _TransactionContext = {
            'conn': conn,
            'cursor': cursor
        }
        self._transaction_context = transaction_context
        return self

    def __exit__(self, exc_type, exc_value, traceback):
        '''
        Close connections. If changes aren't committed then
        they are lost. If any exception is thrown then connection
        is closed safely and exception is propagate.
        '''
        context = self._transaction_context
        context["cursor"].close()
        context["conn"].close()
        self._transaction_context = None

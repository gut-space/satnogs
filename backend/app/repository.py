from configparser import Error
from datetime import datetime
from functools import wraps
from typing import Any, Dict, List, TypedDict, NewType, Sequence, NoReturn, Union, Optional, Tuple

import psycopg2

from psycopg2 import connect

Connection = Any
Cursor = Any

class RepositoryError(Exception):
    def __init__(self, message: str):
        super().__init__(message)

class VersionTableNotExistsError(RepositoryError):
    def __init__(self):
        super().__init__("Version table not exists. Your database is in unsupported version. Migrate it manually to 05 version")

class VersionNotSetError(RepositoryError):
    def __init__(self):
        super().__init__("Table version is empty")

class TransactionContext(TypedDict):
    conn: Connection
    cursor: Cursor

ObservationId = NewType("ObservationId", int)
StationId = NewType("StationId", int)
SatelliteId = NewType("SatelliteId", int)
StationPhotoId = NewType("StationPhotoId", int)

class Observation(TypedDict):
    obs_id: ObservationId
    aos: datetime
    tca: datetime
    los: datetime
    sat_id: SatelliteId
    sat_name: str
    filename: str
    thumbfile: str
    notes: str
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

def use_cursor(f):
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
    def __init__(self, config=None):
        if config is None:
            import app
            config = app.config["database"]
        self._config = config
        self._transaction_context: Optional[TransactionContext] = None # type: ignore

    @staticmethod
    def _row_to_object(row: Sequence[Any], columns: Sequence[str]) -> Dict[str, Any]:
        obj = {}
        for label, value in zip(columns, row):
            obj[label] = value
        return obj

    @property
    def is_pending_transaction(self):
        return self._transaction_context is not None

    @property
    def _cursor(self) -> Cursor:
        context = self._transaction_context
        return context.get("cursor")

    @use_cursor
    def read_observations(self, limit:int=100, offset:int=0) -> Sequence[Observation]:
        q = "SELECT obs_id, aos, " \
                "tca, los, " \
                "sat_id, sat_name, " \
                "filename, 'thumb-' || filename, " \
                "station_id, notes " \
            "FROM observations " \
            "ORDER BY aos DESC " \
            "LIMIT %s OFFSET %s"
        cursor = self._cursor
        cursor.execute(q, (limit, offset))

        rows = cursor.fetchall()
        columns = ["obs_id", "aos", "tca", "los",
                    "sat_id", "sat_name",
                    "filename", "thumbfile", 
                    "station_id", "notes"]
        items: List[Observation] = []
        
        for row in rows:
            item: Observation = Repository._row_to_object(row, columns) # type: ignore
            items.append(item)

        return items
        
    @use_cursor
    def read_observation(self, obs_id: ObservationId) -> Optional[Observation]:
        q = "SELECT obs_id, aos, " \
                "tca, los, sat_name, " \
                "filename, 'thumb-' || filename, " \
                "station_id, notes " \
            "FROM observations " \
            "WHERE obs_id = %s" \
            "ORDER BY aos DESC " \
            "LIMIT 1"
        cursor = self._cursor
        cursor.execute(q, (obs_id,))

        row = cursor.fetchone()
        if row is None:
            return None

        columns = ["obs_id", "aos", "tca", "los", "sat_name", "filename", "thumbfile", "station_id", "notes"]
        
        item: Observation = Repository._row_to_object(row, columns) # type: ignore

        return item    
    
    @use_cursor
    def insert_observation(self, observation: Observation) -> None:
        cursor = self._cursor
        cursor.execute(
            "INSERT INTO observations (aos, tca, los, sat_id, sat_name, filename, notes, station_id)"
            "VALUES (%(aos)s, %(tca)s, %(los)s, %(sat_id)s, %(sat_name)s, %(filename)s, %(notes)s, %(station_id)s);",
            {
                'aos': observation["aos"].isoformat(),
                'tca': observation['tca'].isoformat(),
                'los': observation['los'].isoformat(),
                'sat_id': observation['sat_id'],
                'sat_name': observation['sat_name'],
                'filename': observation['filename'],
                'notes': observation['notes'],
                'station_id': observation['station_id']
            }
        )

    @use_cursor
    def read_satellite(self, sat: Union[SatelliteId, str]) -> Optional[Satellite]:
        if type(sat) == str:
            q = "SELECT sat_id, sat_name FROM satellites WHERE sat_name = %s LIMIT 1;"
        else:
            q = "SELECT sat_id, sat_name FROM satellites WHERE sat_id = %s LIMIT 1;"
        cursor = self._cursor
        cursor.execute(q, (sat,))

        row = cursor.fetchone()

        if row is None:
            return None

        columns = ["sat_id", "sat_name"]
        item: Satellite = Repository._row_to_object(row, columns) # type: ignore
        return item

    @use_cursor
    def read_stations(self, limit=100, offset=0) -> Sequence[Tuple[Station, int, datetime]]:
        q = "SELECT s.station_id, s.name, s.lon, s.lat, s.descr, s.config, s.registered, " \
                    "COUNT(o), MAX(o.los) " \
            "FROM stations s " \
            "LEFT JOIN observations o ON s.station_id = o.station_id " \
            "GROUP BY s.station_id " \
            "LIMIT %s OFFSET %s"

        station_columns = ["station_id", "name", "lon", "lat", "descr", "config", "registered"]

        cursor = self._cursor
        cursor.execute(q, (limit, offset))
        rows = cursor.fetchall()
        items = []

        for row in rows:
            station: Station = Repository._row_to_object(row[:len(station_columns)], station_columns) # type: ignore
            count: int
            lastobs: datetime
            count, lastobs = row[len(station_columns):]
            item = (station, count, lastobs)
            items.append(item)

        return items

    @use_cursor
    def read_station(self, id_: StationId) -> Optional[Tuple[Station, int, datetime]]:
        q = "SELECT s.station_id, s.name, s.lon, s.lat, s.descr, s.config, s.registered, " \
                    "COUNT(o), MAX(o.los) " \
            "FROM stations s " \
            "LEFT JOIN observations o ON s.station_id = o.station_id " \
            "WHERE s.station_id = %s " \
            "GROUP BY s.station_id " \
            "LIMIT 1"

        station_columns = ["station_id", "name", "lon", "lat", "descr", "config", "registered"]

        cursor = self._cursor
        cursor.execute(q, (id_,))
        row = cursor.fetchone()
        if row is None:
            return row

        station: Station = Repository._row_to_object(row[:len(station_columns)], station_columns) # type: ignore
        count: int
        lastobs: datetime
        count, lastobs = row[len(station_columns):]
        return station, count, lastobs

    @use_cursor
    def read_station_photos(self, id_: StationId) -> Sequence[StationPhoto]:
        q = "SELECT photo_id, station_id, sort, filename, descr " \
            "FROM station_photos " \
            "WHERE station_id = %s"

        cursor = self._cursor
        cursor.execute(q, (id_,))
        rows = cursor.fetchall()

        columns = ["photo_id", "station_id", "sort", "filename", "descr"]

        items = []
        for row in rows:
            item: StationPhoto = Repository._row_to_object(row, columns) # type: ignore
            items.append(item)
        return items

    @use_cursor
    def read_station_secret(self, station_id: StationId) -> Optional[bytes]:
        query = "SELECT secret FROM stations WHERE station_id = %s"
        cursor = self._cursor
        cursor.execute(query, (station_id,))
        row = cursor.fetchone()
        if row is None:
            return None
        return row[0].tobytes()

    @use_cursor
    def get_database_version(self) -> int:
        exists_query = "SELECT EXISTS ( " \
                        "SELECT FROM information_schema.tables " \
                        "WHERE table_schema = 'public' " \
                            "AND  table_name = 'version' " \
                        ");"
        cursor = self._cursor
        cursor.execute(exists_query)
        is_table_version_exists = cursor.fetchone()[0]
        if not is_table_version_exists:
            raise VersionTableNotExistsError()

        version_query = 'SELECT "version" FROM "version" LIMIT 1'
        cursor.execute(version_query)
        row = cursor.fetchone()
        if row is None:
            raise VersionNotSetError()
        return row[0]

    @use_cursor
    def execute_raw_query(self, query):
        cursor = self._cursor
        cursor.execute(query)

    def transaction(self):
        return Transaction(self)

    
        
class Transaction:
    def __init__(self, repository: Repository):
        self._repository = repository

    @property
    def _transaction_context(self) -> Optional[TransactionContext]:
        repository = self._repository
        return repository._transaction_context

    @_transaction_context.setter
    def _transaction_context(self, transaction_context: Optional[TransactionContext]):
        self._repository._transaction_context = transaction_context

    def commit(self):
        context = self._transaction_context
        conn = context["conn"]
        conn.commit()

    def rollback(self):
        context = self._transaction_context
        conn = context["conn"]
        conn.rollback()

    def __enter__(self):
        config = self._repository._config
        conn: Connection = psycopg2.connect(**config)
        cursor: Cursor = conn.cursor()
        transaction_context: TransactionContext = {
            'conn': conn,
            'cursor': cursor
        }
        self._transaction_context = transaction_context
        return self

    def __exit__(self, exc_type, exc_value, traceback):
        context = self._transaction_context
        context["cursor"].close()
        context["conn"].close()
        self._transaction_context = None
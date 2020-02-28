from datetime import datetime
from functools import wraps
from typing import Any, Dict, List, TypedDict, NewType, Sequence, NoReturn, Union, Optional, Tuple

import psycopg2

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
        self_obj = args[0]
        config = self_obj._config

        kwargs.pop("conn", None)
        kwargs.pop("cursor", None)

        with psycopg2.connect(**config) as conn:
            with conn.cursor() as cursor:
                res = f(*args, **kwargs, conn=conn, cursor=cursor)
                conn.commit()
        return res

    return wrapper

class Repository:
    def __init__(self, config=None):
        if config is None:
            import app
            config = app.config["database"]
        self._config = config

    @staticmethod
    def _row_to_object(row: Sequence[Any], columns: Sequence[str]) -> Dict[str, Any]:
        obj = {}
        for label, value in zip(columns, row):
            obj[label] = value
        return obj

    @use_cursor
    def read_observations(self, limit:int=100, offset:int=0, conn=None, cursor=None) -> Sequence[Observation]:
        q = "SELECT obs_id, aos, " \
                "tca, los, " \
                "sat_id, sat_name, " \
                "filename, 'thumb-' || filename, " \
                "station_id, notes " \
            "FROM observations " \
            "ORDER BY aos DESC " \
            "LIMIT %s OFFSET %s"
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
    def read_observation(self, obs_id: ObservationId, conn=None, cursor=None) -> Optional[Observation]:
        q = "SELECT obs_id, aos, " \
                "tca, los, sat_name, " \
                "filename, 'thumb-' || filename, " \
                "station_id, notes " \
            "FROM observations " \
            "WHERE obs_id = %s" \
            "ORDER BY aos DESC " \
            "LIMIT 1"
        cursor.execute(q, (obs_id,))

        row = cursor.fetchone()
        if row is None:
            return None

        columns = ["obs_id", "aos", "tca", "los", "sat_name", "filename", "thumbfile", "station_id", "notes"]
        
        item: Observation = Repository._row_to_object(row, columns) # type: ignore

        return item    
    
    @use_cursor
    def insert_observation(self, observation: Observation, conn=None, cursor=None) -> None:
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
    def read_satellite(self, sat: Union[SatelliteId, str], conn=None, cursor=None) -> Optional[Satellite]:
        if type(sat) == str:
            q = "SELECT sat_id, sat_name FROM satellites WHERE sat_name = %s LIMIT 1;"
        else:
            q = "SELECT sat_id, sat_name FROM satellites WHERE sat_id = %s LIMIT 1;"
        cursor.execute(q, (sat,))

        row = cursor.fetchone()

        if row is None:
            return None

        columns = ["sat_id", "sat_name"]
        item: Satellite = Repository._row_to_object(row, columns) # type: ignore
        return item

    @use_cursor
    def read_stations(self, limit=100, offset=0, conn=None, cursor=None) -> Sequence[Tuple[Station, int, datetime]]:
        q = "SELECT s.station_id, s.name, s.lon, s.lat, s.descr, s.config, s.registered, " \
                    "COUNT(o), MAX(o.los) " \
            "FROM stations s " \
            "LEFT JOIN observations o ON s.station_id = o.station_id " \
            "GROUP BY s.station_id " \
            "LIMIT %s OFFSET %s"

        station_columns = ["station_id", "name", "lon", "lat", "descr", "config", "registered"]

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
    def read_station(self, id_: StationId, conn=None, cursor=None) -> Optional[Tuple[Station, int, datetime]]:
        q = "SELECT s.station_id, s.name, s.lon, s.lat, s.descr, s.config, s.registered, " \
                    "COUNT(o), MAX(o.los) " \
            "FROM stations s " \
            "LEFT JOIN observations o ON s.station_id = o.station_id " \
            "WHERE s.station_id = %s " \
            "GROUP BY s.station_id " \
            "LIMIT 1"

        station_columns = ["station_id", "name", "lon", "lat", "descr", "config", "registered"]

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
    def read_station_photos(self, id_: StationId, conn=None, cursor=None) -> Sequence[StationPhoto]:
        q = "SELECT photo_id, station_id, sort, filename, descr " \
            "FROM station_photos " \
            "WHERE station_id = %s"

        cursor.execute(q, (id_,))
        rows = cursor.fetchall()

        columns = ["photo_id", "station_id", "sort", "filename", "descr"]

        items = []
        for row in rows:
            item: StationPhoto = Repository._row_to_object(row, columns) # type: ignore
            items.append(item)
        return items

    @use_cursor
    def read_station_secret(self, station_id: StationId, conn=None, cursor=None) -> Optional[bytes]:
        query = "SELECT secret FROM stations WHERE station_id = %s"
        cursor.execute(query, (station_id,))
        row = cursor.fetchone()
        if row is None:
            return None
        return row[0].tobytes()


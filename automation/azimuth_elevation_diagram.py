import datetime
from dateutil import tz
from typing import List, Optional

from datetimerange import DateTimeRange
from orbit_predictor.locations import Location
from matplotlib import pyplot as plt
import plotille

from orbitdb import OrbitDatabase
from utils import open_config, get_location

def plot(sat_id: str,
        aos: datetime.datetime, los: datetime.datetime,
        location: Optional[Location]=None,
        time_step: Optional[datetime.timedelta]=None,
        width=50, height=20, scale_elevation=True, axis_in_local_time=True):

    tzutc = tz.tzutc()
    assert aos.tzinfo == tzutc
    assert los.tzinfo == tzutc

    if time_step is None:
        time_step = datetime.timedelta(minutes=1)
    if location is None:
        config = open_config()
        location = Location(*get_location(config))

    db = OrbitDatabase()
    predictor = db.get_predictor(sat_id)

    date_series: List[datetime.datetime] = []
    azimuth_series: List[float] = []
    elevation_series: List[float] = []

    for date in DateTimeRange(aos, los).range(time_step):
        position = predictor.get_position(date)
        az, el = location.get_azimuth_elev_deg(position)
        if axis_in_local_time:
            date = date.astimezone(tz.tzlocal())
        date_series.append(date) # type: ignore
        azimuth_series.append(az)
        # We scale elevation, because plotille library allow draw only one
        # Y axis.
        if scale_elevation:
            el = el * 4
        elevation_series.append(el)

    if len(date_series) < 2:
        print("No plot. Not enough data.")
        return

    fig = plotille.Figure()
    fig.width = width
    fig.height = height
    fig.color_mode = 'byte'
    fig.set_y_limits(0, 360)
    fig.plot(date_series, azimuth_series, label="Azimuth", lc=25)
    elevation_label = "Elevation"
    if scale_elevation:
        elevation_label += " * 4"
    else:
        fig.plot(date_series, [90,] * len(date_series), interp=None, label="Y=90")
    fig.plot(date_series, elevation_series, label=elevation_label, lc=1)
    fig.y_label = "Degrees"
    x_label = "Time (%s)" % ("local" if axis_in_local_time else "UTC",) 
    fig.x_label = x_label
    print(fig.show(legend=True))

if __name__ == '__main__':
    sat = "METEOR-M 2"
    aos = datetime.datetime(2020, 3, 21, 17, 22, 0, tzinfo=tz.tzutc())
    los = datetime.datetime(2020, 3, 21, 17, 37, 0, tzinfo=tz.tzutc())
    plot(sat, aos, los)

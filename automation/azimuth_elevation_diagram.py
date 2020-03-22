import datetime
from dateutil import tz
import math
from typing import List, Optional, Sequence

from datetimerange import DateTimeRange
from orbit_predictor.locations import Location
from matplotlib import pyplot as plt
import plotille

from orbitdb import OrbitDatabase
from utils import open_config, get_location

COLOR_BLUE = 25
COLOR_RED = 1

def _calculate_series(sat_id: str,
        aos: datetime.datetime, los: datetime.datetime,
        location: Optional[Location]=None,
        time_step: Optional[datetime.timedelta]=None):

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
        date_series.append(date) # type: ignore
        azimuth_series.append(az)
        elevation_series.append(el)

    return date_series, azimuth_series, elevation_series

def plot(sat_id: str,
        aos: datetime.datetime, los: datetime.datetime,
        location: Optional[Location]=None,
        time_step: Optional[datetime.timedelta]=None,
        width=50, height=20, scale_elevation=True, axis_in_local_time=True, scale_polar=0.5):

    date_series, azimuth_series, elevation_series = _calculate_series(sat_id, aos, los, location, time_step)
    plot_polar_azimuth_elevation(azimuth_series, elevation_series,
        int(width * scale_polar), int(height * scale_polar))
    plot_azimuth_and_elevation_from_time(date_series, azimuth_series, elevation_series,
        width=width, height=height,
        scale_elevation=scale_elevation, axis_in_local_time=axis_in_local_time)


def plot_azimuth_and_elevation_from_time(date_series: Sequence[datetime.datetime],
        azimuth_series: Sequence[float], elevation_series: Sequence[float],
        width=50, height=20, scale_elevation=True, axis_in_local_time=True):
    # We scale elevation, because plotille library allow draw only one Y axis.
    if scale_elevation:
        elevation_series = [el *4 for el in elevation_series]
    if axis_in_local_time:
        target_tz = tz.tzlocal()
        date_series = [d.astimezone(target_tz) for d in date_series]

    if len(date_series) < 2:
        print("No plot. Not enough data.")
        return

    fig = plotille.Figure()
    fig.width = width
    fig.height = height
    fig.color_mode = 'byte'
    fig.set_y_limits(0, 360)
    fig.plot(date_series, azimuth_series, label="Azimuth", lc=COLOR_BLUE)
    elevation_label = "Elevation"
    if scale_elevation:
        elevation_label += " * 4"
    else:
        fig.plot(date_series, [90,] * len(date_series), interp=None, label="Y=90")
    fig.plot(date_series, elevation_series, label=elevation_label, lc=COLOR_RED)
    fig.y_label = "Degrees"
    x_label = "Time (%s)" % ("local" if axis_in_local_time else "UTC",) 
    fig.x_label = x_label
    print(fig.show(legend=True))

def plot_polar_azimuth_elevation(azimuth_series: Sequence[float], elevation_series: Sequence[float],
        width=50, height=20):
    xmin, xmax, ymin, ymax = -1, 1.05, -1, 1.05

    canvas = plotille.Canvas(width, height, xmin=xmin, xmax=xmax, ymin=ymin, ymax=ymax, color_mode="byte")
    canvas.line(-1, 0, 1, 0)
    canvas.line(0, -1, 0, 1)
    DELIMITER_HALF = 0.05
    for d in [-1 + i * 1/3 for i in range(0,7)]:
        canvas.line(d, -DELIMITER_HALF, d, DELIMITER_HALF)
        canvas.line(-DELIMITER_HALF, d, DELIMITER_HALF, d)

    points = []
    for az, el in zip(azimuth_series, elevation_series):
        d = 1 - el / 90
        az_rad = az * (math.pi / 180)
        x = d * math.sin(az_rad)
        y = d * math.cos(az_rad)
        points.append((x, y))
    
    if len(points) == 0:
        return

    first_point_iterator = iter(points)
    second_point_iterator = iter(points)
    first_point = next(second_point_iterator)
    edges = zip(first_point_iterator, second_point_iterator)

    for (x1, y1), (x2, y2) in edges:
        canvas.line(x1, y1, x2, y2, color=COLOR_BLUE)
        #canvas.point(x1, y1, color=COLOR_BLUE)

    canvas.point(first_point[0], first_point[1], color=COLOR_RED)
    print(canvas.plot())
    print("Red dot is start point\n")

if __name__ == '__main__':
    sat = "METEOR-M 2"
    aos = datetime.datetime(2020, 3, 22, 15, 26, 0, tzinfo=tz.tzutc())
    los = datetime.datetime(2020, 3, 22, 15, 38, 0, tzinfo=tz.tzutc())
    plot(sat, aos, los, scale_polar=0.25)


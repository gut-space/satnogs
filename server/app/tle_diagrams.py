from datetime import datetime, timedelta
import io
import math
import sys
from collections import namedtuple
from typing import List, Sequence, Tuple

if sys.version_info >= (3, 8):
    from typing import TypedDict
else:
    from typing_extensions import TypedDict

from matplotlib import pyplot as plt
from matplotlib.backends.backend_agg import FigureCanvasAgg as FigureCanvas
from orbit_predictor.sources import get_predictor_from_tle_lines
from orbit_predictor.locations import Location as PredictLocation

Location = namedtuple("Location", ("latitude", "longitude", "elevation"))

def _calculate_series(location: Location, tle: Sequence[str],
        aos: datetime, los: datetime,
        time_step: timedelta) -> Tuple[Sequence[datetime],
        Sequence[float], Sequence[float]]:
    '''Calculate data for plot diagrams'''
    date_series: List[datetime] = []
    azimuth_series: List[float] = []
    elevation_series: List[float] = []

    location = PredictLocation("server", *location)
    predictor = get_predictor_from_tle_lines(tle)

    date: datetime = aos
    while (date <= los):
        position = predictor.get_position(date)
        az, el = location.get_azimuth_elev_deg(position)

        date_series.append(date)
        azimuth_series.append(az)
        elevation_series.append(el)

        date += time_step

    return date_series, azimuth_series, elevation_series

def _produce_azimuth_elevation_by_time_figure(dates: Sequence[datetime],
        azimuths: Sequence[float], elevations: Sequence[float]) -> plt.Figure:
    '''Return figure with azimuth/elevation plot by time. X axis contains dates.
        Plot has two Y axis. Colors are compatible with gPredict.'''
    fig: plt.Figure = plt.figure()
    ax1: plt.Axes = fig.add_subplot()

    ax1.plot(dates, azimuths, 'b')
    ax1.set_ylim(0, 360)
    ax1.set_ylabel("Azimuth [deg]")
    ax1.set_xlabel("Time")

    ax2 = ax1.twinx()
    ax2.plot(dates, elevations, 'r')
    ax2.set_ylim(0, 90)
    ax2.set_ylabel("Elevation [deg]")

    fig.legend(("Azimuth", "Elevation"))
    return fig

def _produce_azimuth_elevation_polar_figure(dates: Sequence[datetime],
        azimuths: Sequence[float], elevations: Sequence[float],
        time_step:timedelta) -> plt.Figure:
    '''Returns figure with azimuth/elevation polar plot. @time_step define
        temporal distance between labels near trajectory.'''
    fig: plt.Figure = plt.figure()
    ax: plt.Axes = fig.add_subplot(projection="polar")
    ax.set_theta_zero_location('N')
    ax.set_theta_direction(-1)
    ax.set_ylim(90, 0)

    angles = [math.radians(az) for az in azimuths]

    ax.plot(angles, elevations)

    previous_date = None
    for date, angle, el in zip(dates, angles, elevations):
        if previous_date is not None and date - previous_date < time_step:
            continue
        ax.annotate(date.strftime("%H:%M"), (angle, el))
        previous_date = date

    return fig

def _save_to_png(figure: plt.Figure) -> io.BytesIO:
    '''Generate PNG from figure and return binary stream.
        @see https://stackoverflow.com/a/50728936'''
    output = io.BytesIO()
    FigureCanvas(figure).print_png(output)
    return output

def generate_polar_plot_png(location: Location, tle: Sequence[str],
        aos: datetime, los: datetime,
        predict_time_step: timedelta=timedelta(seconds=30),
        polar_time_step: timedelta=timedelta(minutes=2, seconds=30)):
    '''
    Return binary stream with azimuth/elevation polar plot in PNG file.

    Parameters
    ==========
    location: Location
        Location of ground station
    tle: two strings
        TLE data
    aos: datetime.datetime
        Acquisition of Signal
    los: datetime.datetime
        Loss of Signal
    predict_time_step: datetime.timedelta, optional
        Step between data samples to predict. Lower produces more accurate
        plot, but increase computation time
    polar_time_step: datetime.timedelta, optional
        Temporal distance between date labels on plot. Higher reduces
        readability.
    '''
    series = _calculate_series(location, tle, aos, los, predict_time_step)
    by_time_figure = _produce_azimuth_elevation_by_time_figure(*series) # type: ignore
    figure = _produce_azimuth_elevation_polar_figure(*series, # type: ignore
            polar_time_step)

    return _save_to_png(figure)

def generate_by_time_plot_png(location: Location, tle: Sequence[str],
        aos: datetime, los: datetime,
        predict_time_step: timedelta=timedelta(seconds=30)):
    '''
    Return binary stream with azimuth/elevation by time plot in PNG file.

    Parameters
    ==========
    location: Location
        Location of ground station
    tle: two strings
        TLE data
    aos: datetime.datetime
        Acquisition of Signal
    los: datetime.datetime
        Loss of Signal
    predict_time_step: datetime.timedelta, optional
        Step between data samples to predict. Lower produces more accurate
        plot, but increase computation time
    '''
    series = _calculate_series(location, tle, aos, los, predict_time_step)
    figure = _produce_azimuth_elevation_by_time_figure(*series) # type: ignore
    return _save_to_png(figure)

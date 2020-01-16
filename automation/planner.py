import datetime
import logging
from collections import namedtuple
import sys
from typing import Iterable, Tuple

from orbit_predictor.sources import NoradTLESource
from orbit_predictor.locations import Location
from orbit_predictor.predictors import PredictedPass
from datetimerange import DateTimeRange

from selectstrategy import aos_priority_strategy, Observation
from utils import COMMENT_PASS_TAG, open_config, get_receiver_command, open_crontab

cron = open_crontab()
strategy = aos_priority_strategy

RECEIVER_COMMAND = get_receiver_command()
NOAA_URL = r"https://celestrak.com/NORAD/elements/noaa.txt"

prediction_config = open_config()

def get_command(name: str, range_: DateTimeRange):
    return RECEIVER_COMMAND + '"%s" "%s"' % (name, range_.end_datetime.isoformat())

def get_passes(config, from_: datetime.datetime, to: datetime.datetime):
    location = Location(config["location"]["name"],
        config["location"]["latitude"], config["location"]["longitude"],
        config["location"]["elevation"])
    source = NoradTLESource.from_url(NOAA_URL)
    satellties = config["satellites"]
    
    init = []
    for sat in satellties:
        aos_at = sat.get("aos_at") or config.get("aos_at") or 0
        max_elevation_greater_than = sat.get("max_elevation_greater_than") or config.get("max_elevation_greater_than") or 0
        predictor = source.get_predictor(sat["name"])
        passes = predictor.passes_over(location, from_, to, max_elevation_greater_than, aos_at_dg=aos_at)
        init += [(sat["name"], p) for p in passes]
    
    selected = strategy(init)
    return selected

def plan_passes(selected: Iterable[Observation]):
    for entry in selected:
        cmd = get_command(entry.data, entry.range)
        job = cron.new(cmd, COMMENT_PASS_TAG)
        job.setall(entry.range.start_datetime)
    cron.write()

def clear():
    cron.remove_all(comment=COMMENT_PASS_TAG)
    cron.write()

def execute(interval):
    start = datetime.datetime.utcnow()
    delta = datetime.timedelta(seconds=interval)
    end = start + delta

    passes = get_passes(prediction_config, start, end)
    clear()
    plan_passes(passes)

if __name__ == '__main__':
    interval = sys.argv[1] if len(sys.argv) > 1 else 24 * 60 * 60
    execute(interval)

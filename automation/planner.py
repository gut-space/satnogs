import datetime
from pprint import pprint
import sys
from typing import Sequence

from orbit_predictor.locations import Location
from datetimerange import DateTimeRange

from selectstrategy import strategy_factory, Observation
from utils import COMMENT_PASS_TAG, set_satellite_defaults, open_config, get_receiver_command, \
                open_crontab, utc_to_local, get_location, Configuration
from orbitdb import OrbitDatabase

RECEIVER_COMMAND = get_receiver_command()

prediction_config = open_config()

def get_command(name: str, range_: DateTimeRange):
    return RECEIVER_COMMAND + '"%s" "%s"' % (name, range_.end_datetime.isoformat())

def get_passes(config: Configuration, from_: datetime.datetime, to: datetime.datetime):
    location = Location(*get_location(config))
    satellties = filter(lambda s: not s.get("disabled", False), config["satellites"])
    strategy_name: str = config.get("strategy", "max-elevation") # type: ignore

    orbit_db = OrbitDatabase(config["norad"])
    strategy = strategy_factory(strategy_name)
    
    init = []
    for sat in satellties:
        set_satellite_defaults(config, sat)
        aos_at = sat["aos_at"]
        max_elevation_greater_than = sat["max_elevation_greater_than"]
        predictor = orbit_db.get_predictor(sat["name"])
        passes = predictor.passes_over(location, from_, to, max_elevation_greater_than, aos_at_dg=aos_at)
        init += [(sat["name"], p) for p in passes]
    
    selected = strategy(init)
    return selected

def plan_passes(selected: Sequence[Observation], cron):
    selected = sorted(selected, key=lambda o: o.pass_.aos)
    for entry in selected:
        cmd = get_command(entry.data, entry.range)
        job = cron.new(cmd, COMMENT_PASS_TAG)
        start_datetime = utc_to_local(entry.range.start_datetime)
        job.setall(start_datetime)
    cron.write()

def clear(cron):
    cron.remove_all(comment=COMMENT_PASS_TAG)
    cron.write()

def execute(interval, cron=None):
    if cron is None:
        cron = open_crontab()
    start = datetime.datetime.utcnow()
    delta = datetime.timedelta(seconds=interval)
    end = start + delta

    passes = get_passes(prediction_config, start, end)
    clear(cron)
    plan_passes(passes, cron)
    return passes

if __name__ == '__main__':
5    interval = int(sys.argv[1]) if len(sys.argv) > 1 else 24 * 60 * 60
    execute(interval)

import datetime
import logging
from collections import namedtuple
from pprint import pprint
import sys
from typing import Iterable, Tuple

from orbit_predictor.locations import Location
from datetimerange import DateTimeRange

from selectstrategy import strategy_factory, Observation
from utils import COMMENT_PASS_TAG, open_config, get_receiver_command, open_crontab, utc_to_local
from orbitdb import OrbitDatabase

RECEIVER_COMMAND = get_receiver_command()

prediction_config = open_config()

def get_command(name: str, range_: DateTimeRange):
    return RECEIVER_COMMAND + '"%s" "%s"' % (name, range_.end_datetime.isoformat())

def get_passes(config, from_: datetime.datetime, to: datetime.datetime):
    location = Location(config["location"]["name"],
        config["location"]["latitude"], config["location"]["longitude"],
        config["location"]["elevation"])
    satellties = filter(lambda s: not getattr(s, "disabled", False), config["satellites"])
    strategy_name = config.get("strategy", "max-elevation")

    orbit_db = OrbitDatabase(config["norad"])
    strategy = strategy_factory(strategy_name)
    
    init = []
    for sat in satellties:
        aos_at = sat.get("aos_at") or config.get("aos_at") or 0
        max_elevation_greater_than = sat.get("max_elevation_greater_than") or config.get("max_elevation_greater_than") or 0
        predictor = orbit_db.get_predictor(sat["name"])
        passes = predictor.passes_over(location, from_, to, max_elevation_greater_than, aos_at_dg=aos_at)
        init += [(sat["name"], p) for p in passes]
    
    selected = strategy(init)
    return selected

def plan_passes(selected: Iterable[Observation], cron):
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
    interval = int(sys.argv[1]) if len(sys.argv) > 1 else 24 * 60 * 60
    passes = execute(interval)
    pprint([(e.pass_, e.range, "CRON: %s" % (utc_to_local(e.range.start_datetime).strftime("%m-%d %H:%M:%S`"))) for e in passes], width=180)
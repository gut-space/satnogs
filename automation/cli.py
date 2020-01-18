import argparse
import datetime
import calendar
import os
from pprint import pprint
import subprocess
import sys

from deepdiff import DeepHash

import planner
from orbitdb import OrbitDatabase
from utils import COMMENT_PLAN_TAG, COMMENT_PASS_TAG, first, \
                get_planner_command, get_receiver_command, open_config, save_config, \
                APP_NAME, open_crontab

def get_interval(job):
    frequency = job.frequency()
    year = datetime.datetime.utcnow().year
    days_in_year = 366 if calendar.isleap(year) else 365
    interval = int(round((days_in_year * 24 * 60 * 60 * 1.0) / frequency))
    return interval

def update_config(config, args, names):
    for name in names:
        if isinstance(name, str):
            config_name, args_name = name, name
        else:
            config_name, args_name = name

        arg = getattr(args, args_name, None)
        if arg is None:
            continue
        
        config[config_name] = getattr(args, args_name)

def get_hash(obj):
    return DeepHash(obj)[obj]

parser = argparse.ArgumentParser(APP_NAME)
subparsers = parser.add_subparsers(help='commands', dest="command")

clear_parser = subparsers.add_parser(
    'clear', help='Clear all schedule receiving')
plan_parser = subparsers.add_parser('plan', help='Schedule planning receiving')
plan_parser.add_argument("--cron", type=str, help='Cron format required. Default "0 4 * * *" for 4:00 AM')
plan_parser.add_argument("--force", action="store_true", default=False, help="Perform planning now")

config_parser = subparsers.add_parser("config", help="Configuration")
replan_config_parser_group = config_parser.add_mutually_exclusive_group()
replan_config_parser_group.add_argument("-r", "--replan", action="store_true", help="Force plan now", dest="replan")
replan_config_parser_group.add_argument("--no-replan", action="store_false", help="No force plan now", dest="replan", default=False)
config_subparsers = config_parser.add_subparsers(help="Configurations", dest="config_command")
location_config_parser = config_subparsers.add_parser("location", help="Change groundstation location")
location_config_parser.add_argument("-lat", "--latitude", type=float, help="Latitude in degrees")
location_config_parser.add_argument("-lng", "--longitude", type=float, help="Longitude in degrees")
location_config_parser.add_argument("-ele", "--elevation", type=float, help="Elevation in meters")
prediction_config_parser = config_subparsers.add_parser("global", help="Change global prediction parameters")
prediction_config_parser.add_argument("-aos", type=int, help="Elevation (in degress) on AOS")
prediction_config_parser.add_argument("-me", "--max-elevation", type=int, help="Max elevation greater than")
satellite_config_parser = config_subparsers.add_parser("sat", help="Satellite configuration")
satellite_config_parser.add_argument("name", type=str, help="Satellite name", nargs='?')
satellite_config_parser.add_argument("-f", "--frequency", type=str, help="Frequency in Hz. Allowed scientific notation.")
satellite_config_parser.add_argument("-aos", type=int, help="Elevation (in degress) on AOS")
satellite_config_parser.add_argument("-me", "--max-elevation", type=int, help="Max elevation greater than")
satellite_config_parser.add_argument("-d", "--delete", action="store_true", default=False, help="Delete satellite")
norad_config_parser = config_subparsers.add_parser("norad", help="Manage sources NORAD data")
norad_config_parser.add_argument("urls", nargs="*", type=str, help="URLs of NORAD data")
norad_config_parser.add_argument("-d", "--delete", action="store_true", default=False, help="Delete NORAD")
norad_config_parser.add_argument("-r", "--refresh", action="store_true", default=False, help="Re-fetch necessary NORAD files")

args = parser.parse_args()
command = args.command

RECEIVER_COMMAND = get_receiver_command()
PLANNER_COMMAND = get_planner_command()

cron = open_crontab()
planner_job = first(cron.find_comment(COMMENT_PLAN_TAG))

if command == "clear":
    cron.remove_all(comment=COMMENT_PASS_TAG)
    cron.remove_all(comment=COMMENT_PLAN_TAG)
    cron.write()
    print("Cleared all existing jobs")
elif command == "plan":

    if planner_job is None:
        args.cron = args.cron or "0 4 * * *"
        planner_job = cron.new(comment=COMMENT_PLAN_TAG, command="placeholder")

    if args.cron is not None:
        planner_job.setall(args.cron)
        interval = get_interval(planner_job)
        planner_job.set_command(PLANNER_COMMAND + str(interval))
        cron.write()
        print("Planner job %s." % (planner_job.description(
            use_24hour_time_format=True, verbose=True)))

    if args.force:
        interval = get_interval(planner_job)
        planner.execute(interval)
        print("Planned receive jobs successful")

    if args.cron is None:
        pass_jobs = cron.find_comment(COMMENT_PASS_TAG)
        print("%s Planner" % (planner_job.description(
            use_24hour_time_format=True, verbose=True)))

        print("\n".join(
            ("%s %s" % (j.description(use_24hour_time_format=True),
                        j.command.replace(RECEIVER_COMMAND, ""))
             for j in pass_jobs)
        ))

elif command == "config":
    config_command = args.config_command

    config = open_config()
    section = config
    init_hash = get_hash(config)

    if config_command == "location":
        section = config["location"]
        update_config(section, args, ("latitude", "longitude", "elevation"))
    elif config_command == "global":
        update_config(config, args, (("aos_at", "aos"), ("max_elevation_greater_than", "max-elevation")))
    elif config_command == "sat":
        section = config["satellites"]
        if args.name is not None:
            name = args.name
            sat = first(section, lambda item: item["name"] == name)
            if sat is None:
                if not hasattr(args, "frequency"):
                    print("Frequency is required for new satellite")
                    sys.exit(1)
                sat = {
                    "name": name,
                }
                section.append(sat)
            if args.delete:
                section.remove(sat)
            else:
                update_config(sat, args, ("frequency", ("aos_at", "aos"), ("max_elevation_greater_than", "max-elevation")))
        elif args.delete:
            section.clear()
    elif config_command == "norad":
        section = config["norad"]
        if args.urls is None:
            if args.delete:
                section.clear()
            elif args.refresh:
                db = OrbitDatabase(section)
                db.refresh_satellites(s.name for s in config["satellites"])
        elif args.urls is not None:
            if args.delete:
                for url in args.urls:
                    section.remove(url)
            elif args.refresh:
                db = OrbitDatabase(args.urls)
                db.refresh_urls()
            else:
                for url in args.urls:
                    if any(u == url for u in section):
                        continue
                    section.append(url)
                else:
                    db = OrbitDatabase(section)
                    print(db)
    is_changed = get_hash(config) != init_hash
    if is_changed:
        save_config(config)
        print("Configuration changed successfully")
        if args.replan:
            planner.execute(get_interval(planner_job))
    pprint(section, sort_dicts=False)
    
else:
    parser.print_help()

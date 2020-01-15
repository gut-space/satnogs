import argparse

from crontab import CronTab

from utils import COMMENT_PLAN_TAG, COMMENT_PASS_TAG, first

parser = argparse.ArgumentParser()
subparsers = parser.add_subparsers(help='commands', dest="command")

clear_parser = subparsers.add_parser('clear', help='Clear all schedule receiving')
plan_parser = subparsers.add_parser('plan', help='Plan receiving')
plan_parser.add_argument("--cron", type=str, help='Cron format required. Default "0 4 * * *" for 4:00 AM')
plan_parser.add_argument("--force", action="store_true", default=False, help="Perform planning now")

config_parser = subparsers.add_parser("config", help="Configuration")
reload_config_parser_group = config_parser.add_mutually_exclusive_group()
reload_config_parser_group.add_argument("-r", "--reload", action="store_true", help="Force plan now", default=True, dest="reload")
reload_config_parser_group.add_argument("--no-reload", action="store_false", help="No force plan now", dest="reload")
config_subparsers = config_parser.add_subparsers(help="Configurations", dest="config_command")
location_config_parser  = config_subparsers.add_parser("location", help="Change groundstation location")
location_config_parser.add_argument("-lat", "--latitude", type=float, help="Latitude in degrees")
location_config_parser.add_argument("-lng", "--longitude", type=float, help="Longitude in degrees")
location_config_parser.add_argument("-ele", "--elevation", type=float, help="Elevation in meters")
prediction_config_parser = config_subparsers.add_parser("location", help="Change prediction parameters")
prediction_config_parser.add_argument("-aos", type=int, help="Elevation (in degress) on AOS")
prediction_config_parser.add_argument("-me", "--max-elevation", type=int, help="Max elevation greater than")
satellite_config_parser = config_subparsers.add_parser("sat", help="Satellite configuration")
satellite_config_parser.add_argument("name", type=str, help="Satellite name")
satellite_config_parser.add_argument("-aos", type=int, help="Elevation (in degress) on AOS")
satellite_config_parser.add_argument("-me", "--max-elevation", type=int, help="Max elevation greater than")
satellite_config_parser.add_argument("--delete", action="store_true", help="Delete satellite")

args = parser.parse_args()
command = args.command

if command == "clear":
    cron = CronTab(tabfile='cron.tab')
    cron.remove_all(comment=COMMENT_PASS_TAG)
    cron.remove_all(comment=COMMENT_PLAN_TAG)
    cron.write()
    print("Cleared all existing jobs")
elif command == "plan":
    cron = CronTab(tabfile='cron.tab')
    planner_job = first(cron.find_comment(COMMENT_PLAN_TAG))

    if planner_job is None:
        args.cron = args.cron or "0 4 * * *"
        planner_job = cron.new(comment=COMMENT_PLAN_TAG)

    if args.cron is not None:
        planner_job.setall(args.cron)
        frequency = planner_job.frequency()
        interval = int(round((365 * 24 * 60 * 60 * 1.0) / frequency))
        planner_job.set_command("python planner.py " + str(interval))
        cron.write()
        print("Planner job %s." % (planner_job.description(use_24hour_time_format=True, verbose=True)))
    else:
        pass_jobs = cron.find_comment(COMMENT_PASS_TAG)
        print("%s Planner" % (planner_job.description(use_24hour_time_format=True, verbose=True)))
        planner_job
        print("\n".join(
            ("%s %s" % (j.description(use_24hour_time_format=True),
                        j.command.replace("python receiver.py ", ""))
            for j in pass_jobs)
        ))

elif command == "config":
    pass
else:
    parser.print_help()


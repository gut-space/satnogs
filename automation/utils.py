import logging
import os
import sys

from crontab import CronTab
import yaml


DEV_ENVIRONEMT =  os.environ.get("DEV_ENVIRONMENT") == '1'

logging.basicConfig(level=logging.DEBUG if DEV_ENVIRONEMT else logging.ERROR, format='%(asctime)s %(levelname)s %(filename)s:%(lineno)d: %(message)s')

APP_NAME = "SatNOG-PG"
COMMENT_PASS_TAG = APP_NAME + "-Pass"
COMMENT_PLAN_TAG = APP_NAME + "-Plan"
CONFIG_PATH = os.path.expanduser("~/.config/%s/config.yml" % (APP_NAME,)) if not DEV_ENVIRONEMT else "config.yml"

def _get_command(directory, filename):
    if directory is None:
        directory = sys.argv[0]
    if not os.path.isdir(directory):
        directory = os.path.dirname(directory)
    path = os.path.join(directory, filename)
    path = os.path.abspath(path)
    return "python3 %s " % path

def get_planner_command(directory=None):
    return _get_command(directory, "planner.py")

def get_receiver_command(directory=None):
    return _get_command(directory, "receiver.py")

DEFAULT_CONFIG = 'aos_at: 0\nlocation:\n  elevation: 138\n  latitude: 54.3833\n  longitude: 18.4667\n  name: Taneczna\nmax_elevation_greater_than: 0\nsatellites:\n- freq: 137.62e6\n  name: NOAA 15\n- freq: 137.9125e6\n  name: NOAA 18\n- freq: 137.1e6\n  name: NOAA 19\n'

def open_crontab() -> CronTab:
    if DEV_ENVIRONEMT:
        filename = "cron.tab"
        if not os.path.exists(filename):
            with open(filename) as _:
                pass
        return CronTab(tabfile="cron.tab")
    else:
        return CronTab(user=True)

def open_config():
    config_path = CONFIG_PATH
    config_exists = os.path.exists(config_path)
    if not config_exists:
        directory = os.path.dirname(config_path)
        os.makedirs(directory, exist_ok=True)
        with open(config_path, "w") as f:
            f.write(DEFAULT_CONFIG)

    with open(config_path) as f:
        return yaml.safe_load(f)

def save_config(config):
    with open(CONFIG_PATH, "w") as f:
        return yaml.safe_dump(config, f)

def first(iterable, condition = lambda x: True):
    """
    Returns the first item in the `iterable` that
    satisfies the `condition`.

    If the condition is not given, returns the first item of
    the iterable.

    Return `None` if no item satysfing the condition is found.

    >>> first( (1,2,3), condition=lambda x: x % 2 == 0)
    2
    >>> first(range(3, 100))
    3
    >>> first( () )
    None
    """
    try:
        return next(x for x in iterable if condition(x))
    except StopIteration:
        return None

class EditWatcher:
    def __init__(self, obj):
        object.__setattr__(self, "_obj", obj)
        object.__setattr__(self, "_edited", False)

    def __getattr__(self, key):
        return getattr(self._obj, key)

    def __setattr__(self, name, value):
        object.__setattr__(self, "_edited", True)
        return setattr(self._obj, name, value)

    def __getitem__(self, key):
        return self._obj[key]

    def __setitem__(self, key, value):
        object.__setattr__(self, "_edited", True)
        self._obj[key] = value

    def is_edited(self):
        return self._edited

    def get_wrapped(self):
        return self._obj

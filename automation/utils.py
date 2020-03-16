import datetime
import logging
import os
import sys
from typing import List, Optional, Iterable, TypeVar, Callable, Union

from crontab import CronTab
import yaml

if sys.version_info[0] == 3 and sys.version_info[1] >= 8:
    from typing import TypedDict, Literal
else:
    from typing_extensions import TypedDict, Literal

DEV_ENVIRONEMT =  os.environ.get("DEV_ENVIRONMENT") == '1'
APP_NAME = "satnogs-gut"
COMMENT_PASS_TAG = APP_NAME + "-Pass"
COMMENT_PLAN_TAG = APP_NAME + "-Plan"
CONFIG_DIRECTORY = os.path.expanduser("~/.config/%s" % (APP_NAME,)) if not DEV_ENVIRONEMT else os.path.abspath("./config")
CONFIG_PATH = os.path.join(CONFIG_DIRECTORY, "config.yml")

logging.basicConfig(level=logging.DEBUG if DEV_ENVIRONEMT else logging.ERROR,
                    format='%(asctime)s %(levelname)s %(filename)s:%(lineno)d: %(message)s',
                    filename=os.path.join(CONFIG_DIRECTORY, "log") if not DEV_ENVIRONEMT else None)


class LocationConfiguration(TypedDict):
    elevation: float
    latitude: float
    longitude: float
    name: str

SATELLITE_SAVE_MODE = Literal["SIGNAL", "PRODUCT", "ALL", "INHERIT"]
GLOBAL_SAVE_MODE = Literal["SIGNAL", "PRODUCT", "ALL", "NONE"]

class SatelliteConfiguration(TypedDict, total=False):
    freq: str
    name: str
    submit: Optional[bool]
    save_to_disk: Optional[SATELLITE_SAVE_MODE]
    aos_at: Optional[int]
    max_elevation_greater_than: Optional[int]
    disabled: Optional[bool]
    recipe: Optional[str]

class ServerConfiguration(TypedDict):
    id: str
    secret: str
    url: str

STRATEGY = Literal["max-elevation", "aos"]

class Configuration(TypedDict):
    aos_at: int
    location: LocationConfiguration
    max_elevation_greater_than: int
    norad: List[str]
    satellites: List[SatelliteConfiguration]
    save_to_disk: Optional[GLOBAL_SAVE_MODE]
    server: ServerConfiguration
    strategy: Optional[STRATEGY]
    submit: Optional[bool]
    obsdir: Optional[str]

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

DEFAULT_CONFIG = 'aos_at: 0\nlocation:\n  elevation: 138\n  latitude: 54.9\n  longitude: 54.9\n  name: Taneczna\nmax_elevation_greater_than: 0\nnorad:\n- https://celestrak.com/NORAD/elements/noaa.txt\n- https://celestrak.com/NORAD/elements/active.txt\nsatellites:\n- freq: 137.62e6\n  name: NOAA 15\n- freq: 137.9125e6\n  name: NOAA 18\n- freq: 137.1e6\n  name: NOAA 19\nserver:\n  id: 1\n  secret: 873730d540e1154cf3203b09546ac1fe\n  url: http://127.0.0.1:5000/receive\nstrategy: max-elevation\n'

def open_crontab() -> CronTab:
    if DEV_ENVIRONEMT:
        path = os.path.join(CONFIG_DIRECTORY, "cron.tab")
        if not os.path.exists(path):
            with open(path) as _:
                pass
        return CronTab(tabfile=path)
    else:
        return CronTab(user=True)

def open_config() -> Configuration:
    config_path = CONFIG_PATH
    config_exists = os.path.exists(config_path)
    if not config_exists:
        directory = os.path.dirname(config_path)
        os.makedirs(directory, exist_ok=True)
        with open(config_path, "w") as f:
            f.write(DEFAULT_CONFIG)

    with open(config_path) as f:
        return yaml.safe_load(f) # type: ignore

def save_config(config: Configuration):
    with open(CONFIG_PATH, "w") as f:
        return yaml.safe_dump(config, f)

T = TypeVar("T")

def first(iterable: Iterable[T], condition: Callable[[T], bool] = lambda x: True) -> Optional[T]:
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

def utc_to_local(utc_dt):
    return utc_dt.replace(tzinfo=datetime.timezone.utc).astimezone(tz=None)

def is_safe_filename_character(c: str) -> bool:
    return c.isalpha() or c.isdigit() or c in (' ', '.', '-', ' ', '_')

def safe_filename(filename: str, replacement: str="_") -> str:
    chars = [c if is_safe_filename_character(c) else replacement for c in filename]
    return "".join(chars).rstrip()

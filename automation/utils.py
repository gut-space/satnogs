import datetime
import dateutil.parser
import logging
import os
import sys
import shutil
from typing import List, Optional, Iterable, TypeVar, Callable, Tuple

from crontab import CronTab
import yaml

if sys.version_info >= (3, 8):
    from typing import TypedDict, Literal
else:
    from typing_extensions import TypedDict, Literal

DEV_ENVIRONMENT =  os.environ.get("DEV_ENVIRONMENT") == '1'
APP_NAME = "satnogs-gut"
COMMENT_PASS_TAG = APP_NAME + "-Pass"
COMMENT_PLAN_TAG = APP_NAME + "-Plan"

CONFIG_DIRECTORY: str = os.environ.get("SATNOGS_GUT_CONFIG_DIR") # type: ignore
if CONFIG_DIRECTORY is None:
    if DEV_ENVIRONMENT:
        CONFIG_DIRECTORY = os.path.abspath("./config")
    else:
        CONFIG_DIRECTORY = os.path.expanduser("~/.config/%s" % (APP_NAME,))

CONFIG_PATH = os.path.join(CONFIG_DIRECTORY, "config.yml")
LOG_FILE = os.path.join(CONFIG_DIRECTORY, "log") if not DEV_ENVIRONMENT else None

if not os.path.exists(CONFIG_DIRECTORY):
    os.makedirs(CONFIG_DIRECTORY, exist_ok=True)

logging.basicConfig(level=logging.DEBUG if DEV_ENVIRONMENT else logging.ERROR,
                    format='%(asctime)s %(levelname)s %(filename)s:%(lineno)d: %(message)s',
                    filename=LOG_FILE)


class LocationConfiguration(TypedDict):
    elevation: float
    latitude: float
    longitude: float
    name: str

SATELLITE_SAVE_MODE = Literal["SIGNAL", "PRODUCT", "ALL", "INHERIT", "NONE"]
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

def open_crontab() -> CronTab:
    if DEV_ENVIRONMENT:
        path = os.path.join(CONFIG_DIRECTORY, "crontab")
        if not os.path.exists(path):
            with open(path, "x") as _:
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
        shutil.copyfile('config.yml.template', config_path)

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


def get_location(config: Configuration) -> Tuple[str, float, float, float]:
    location = (config["location"]["name"],
            config["location"]["latitude"], config["location"]["longitude"],
            config["location"]["elevation"])
    return location

def set_satellite_defaults(config: Configuration, satellite: SatelliteConfiguration):
    '''
    If satellite structure doesn't contains optional values
    then they will be set using inherited, global configuration.
    '''
    if 'submit' not in satellite:
        global_submit = config.get('submit', None)
        if global_submit is None:
            global_submit = True
        satellite['submit'] = global_submit
    if 'save_to_disk' not in satellite or satellite['save_to_disk'] == 'INHERIT':
        global_ = config.get('save_to_disk')
        if global_ is None:
            global_ = "NONE"
        satellite["save_to_disk"] = global_
    if 'aos_at' not in satellite:
        global_ = config.get('aos_at')
        if global_ is None:
            global_ = 0
        satellite['aos_at'] = global_
    if 'max_elevation_greater_than' not in satellite:
        global_ = config.get('max_elevation_greater_than')
        if global_ is None:
            global_ = 0
        satellite['max_elevation_greater_than'] = global_
    if 'disabled' not in satellite:
        satellite['disabled'] = False

def get_satellite(config: Configuration, sat: str) -> SatelliteConfiguration:
    '''
    Search for satellite configuration. Throw LookupError if not found.
    If found then omitted optional fields will be set using inherited, global
    configuration.
    '''
    satellites = config['satellites']
    satellite = first(satellites, lambda s: s['name'] == sat)
    if satellite is None:
        raise LookupError("Satellite %s not found" % (sat,))
    set_satellite_defaults(config, satellite)
    return satellite

def from_iso_format(raw: str) -> datetime.datetime:
    if sys.version_info <= (3, 6):
        return dateutil.parser.isoparse(raw)
    else:
        return datetime.datetime.fromisoformat(raw)

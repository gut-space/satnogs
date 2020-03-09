import datetime
import os
import subprocess
import sys
from typing import Iterable, Tuple
import uuid

from utils import SatelliteConfiguration

if sys.version_info[0] == 3 and sys.version_info[1] >= 8:
    from typing import Literal
else:
    from typing_extensions import Literal

RECIPE_DIR = os.path.split(os.path.abspath(__file__))[0]
BASE_DIR = "/tmp/observations_tmp"
os.makedirs(BASE_DIR, exist_ok=True)

def get_recipe(sat: SatelliteConfiguration) -> str:
    if "recipe" in sat:
        recipe = sat["recipe"]
    elif sat["name"].startswith("NOAA"):
        recipe = "noaa-apt"
    else:
        raise LookupError("Unknown recipe")

    recipe_filename = os.path.join(RECIPE_DIR, recipe + ".sh")
    if os.path.exists(recipe_filename):
        return recipe_filename
    else:
        raise LookupError("Recipe not exists")

def execute_recipe(sat: SatelliteConfiguration, los: datetime.datetime) -> Iterable[Tuple[Literal["signal", "product"], str]]:
    recipe_path = get_recipe(sat)

    uid = uuid.uuid4()
    base_path = os.path.join(BASE_DIR, str(uid))
    now = datetime.datetime.utcnow()
    record_interval = los - now
    record_seconds = record_interval.total_seconds()

    output_raw = subprocess.check_output([recipe_path, base_path, sat["freq"], str(record_seconds)])
    output = output_raw.decode()

    results = []
    for line in output.split("\n"):
        line = line.strip()
        parts = line.split(maxsplit=2)
        if len(parts) != 3:
            continue
        mark, category, path = parts
        if mark != "!!":
            continue
        if not category.endswith(":"):
            continue
        if not os.path.exists(path):
            continue
        category = category.rstrip(":").lower()
        results.append((category, path))
    return results

def get_recipe_names():
    filenames = os.listdir(RECIPE_DIR)
    recipes = []
    for filename in filenames:
        if not filename.endswith(".sh"):
            continue
        path = os.path.join(RECIPE_DIR, filename)
        if not os.path.isfile(path):
            continue
        recipe_name, _ = os.path.splitext(filename)
        recipes.append(recipe_name)
    return recipes
        

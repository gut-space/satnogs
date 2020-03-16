import datetime
import logging
import os
import subprocess
import sys
from typing import Iterable, List, Tuple
import uuid

from utils import SatelliteConfiguration

if sys.version_info[0] == 3 and sys.version_info[1] >= 8:
    from typing import Literal
else:
    from typing_extensions import Literal

'''
The different satellites require different software and configuration. We need
a possibility to add new configurations without rewrite our receive scripts or
write wrappers in Python for each new subprogram.
This is a recipe-based solution. "Recipe" is a shell script which is responsible
for receive signal and decode it.

As input each recipe gets three parameters:

* Base path - it is a prefix for all files created by script. It contains
              writable directory and random, unique token. It ensure that any
            file with this prefix may be safe created.
* Frequency - it is frequency for SDR. It is passed as parameter, because some
              satellites may to use the same receive and decode flow as NOAA
              familly
* LOS date - it is date when script should stop SDR

As output the script should print on standard output in format:
    !! CATEGORY: PATH
where CATEGORY is category of file. Now I use "Signal" for initial WAV file and
"Product" for decoded imagery. I think that we will need a category for waterfall
and text, binary data in future.

User should have a possibility to execute recipe without using Python code.

Recipe is responsible for cleanup all created files excluded the files printed
as output. These files are clean up by Python code.

User has a possibility to select recipe by "recipe" parameter in satellite
config. Now it is optional and script try to deduce recipe based on satellite. 
(For example if recipe isn't provided and name starts with NOAA then we use
recipe for NOAA).

All recipes must be located in directory with this file ("recipes"), have ".sh"
extensions and set execute rights for owner.

Your shell script should starts with the shebang (e.g. #!/bin/sh).
'''

RECIPE_DIR = os.path.split(os.path.abspath(__file__))[0]
BASE_DIR = "/tmp/observations_tmp"
os.makedirs(BASE_DIR, exist_ok=True)

def get_recipe(sat: SatelliteConfiguration) -> str:
    '''
    Returns path to recipe file assigned with passed satellite.
    If recipe doesn't exist throw LookupError.
    
    Function check "recipe" field in passed configuration for recipe.
    If it is empty then check built-in list with compatible recipes.
    '''
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
        raise LookupError("Recipe doesn't exist")

def execute_recipe(sat: SatelliteConfiguration, los: datetime.datetime) -> Iterable[Tuple[Literal["signal", "product"], str]]:
    '''
    Execute recipe for passed satellite and return results.

    Return collection of tuples with category and path.
    If no recipe found then throw LookupError.

    We use "signal" category for not processed, received signal file
    and "product" for finish data (e. q. imagery) extracted from signal.
    You may get multiple files with the same category.

    Caller is responsible for cleanup results.
    You need delete or move returned files when you don't need them.
    '''
    recipe_path = get_recipe(sat)

    uid = uuid.uuid4()
    base_path = os.path.join(BASE_DIR, str(uid))
    now = datetime.datetime.utcnow()
    record_interval = los - now
    record_seconds = record_interval.total_seconds()

    try:
        output_raw = subprocess.check_output([recipe_path, base_path, sat["freq"], str(record_seconds)])
    except subprocess.CalledProcessError as ex:
        logging.error("Command %s exited with code: %d. Output: %s" % (ex.cmd, int(ex.returncode), ex.output.decode()))
        output_raw = ex.output
        
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

def get_recipe_names() -> List[str]:
    '''Returns all recipe names.'''
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
        

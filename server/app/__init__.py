try:
    from configparser import ConfigParser, NoSectionError, NoOptionError
except ImportError:
    from ConfigParser import ConfigParser, NoSectionError, NoOptionError

import os

from flask import Flask
from app.repository import User

app = Flask(__name__, template_folder='../templates')

root_dir = os.path.dirname(os.path.realpath(__file__))
root_dir = os.path.dirname(root_dir)
ini_path = os.path.join(root_dir, 'satnogs.ini')

try:

    config = ConfigParser()
    config.optionxform = str
    config.read(ini_path)

    for key, value in config.defaults().items():
        app.config[key] = value

    for section_name in config.sections():
        app.config[section_name] = {}
        section = config[section_name]
        for key, value in section.items():
            app.config[section_name][key] = value

except IOError as e:
    raise Exception("Unable to read %s file: %s" % (ini_path, e) )
except NoSectionError as e:
    raise Exception("Unable to find section 'database' in the %s file: %s" % (ini_path, e) )
except NoOptionError as e:
    raise Exception("Unable to find option in 'database' section in the %s file: %s" % (ini_path, e) )

from app import routes
from app import template_globals
from app.utils import get_footer

footer = get_footer()
app.jinja_env.globals["footer"] = footer



try:
    from configparser import ConfigParser, NoSectionError, NoOptionError
except ImportError:
    from ConfigParser import ConfigParser, NoSectionError, NoOptionError

import os
from flask import Flask

app = Flask(__name__, template_folder='../templates')

try:
    rootdir = os.path.dirname(os.path.realpath(__file__))
    rootdir = os.path.dirname(rootdir)
    inipath = os.path.join(rootdir, 'satnogs.ini')

    config = ConfigParser()
    config.read(inipath)

    for key, value in config.defaults().items():
        app.config[key] = value

    for section_name in config.sections():
        app.config[section_name] = {}
        section = config[section_name]
        for key, value in section.items():
            app.config[section_name][key] = value
    
except IOError as e:
    raise Exception("Unable to read %s file: %s" % (inipath, e) )
except NoSectionError as e:
    raise Exception("Unable to find section 'database' in the %s file: %s" % (inipath, e) )
except NoOptionError as e:
    raise Exception("Unable to find option in 'database' section in the %s file: %s" % (inipath, e) )


from app import routes



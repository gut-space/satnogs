try:
    from configparser import ConfigParser, NoSectionError, NoOptionError
except ImportError:
    from ConfigParser import ConfigParser, NoSectionError, NoOptionError

import os

class SrvConfig:
    db_host = ""
    db_user = ""
    db_pass = ""
    db_name = ""
    db_debug = False

def getConfig():
    config = ConfigParser()
    cfg = SrvConfig()

    try:
        rootdir = os.path.dirname(os.path.realpath(__file__))
        rootdir = rootdir[:rootdir.rfind(os.path.sep)]
        inipath = rootdir + os.path.sep + 'satnogs.ini'

        config.read(inipath)
        cfg.db_host = config.get('server', 'db_host')
        cfg.db_user = config.get('server', 'db_user')
        cfg.db_pass = config.get('server', 'db_pass')
        cfg.db_name = config.get('server', 'db_name')
        cfg.debug = config.get('server', 'debug')
    except IOError as e:
        raise Exception("Unable to read %s file: %s" % (inipath, e) )
    except NoSectionError as e:
        raise Exception("Unable to find section 'server' in the %s file: %s" % (inipath, e) )
    except NoOptionError as e:
        raise Exception("Unable to find option in 'server' section in the %s file: %s" % (inipath, e) )

    return cfg



try:
    from configparser import ConfigParser, NoSectionError, NoOptionError
except ImportError:
    from ConfigParser import ConfigParser, NoSectionError, NoOptionError

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
        config.read('satnogs.ini')
        cfg.db_host = config.get('server', 'db_host')
        cfg.db_user = config.get('server', 'db_user')
        cfg.db_pass = config.get('server', 'db_pass')
        cfg.db_name = config.get('server', 'db_name')
        cfg.debug = config.get('server', 'debug')
    except IOError as e:
        raise Exception("Unable to read satnogs.ini file: %s" % e)
    except NoSectionError as e:
        raise Exception("Unable to find section 'server' in the satnogs.init file: %s" % e)
    except NoOptionError as e:
        raise Exception("Unable to find option in 'server' section in the satnogs.ini file: %s" % e)

    return cfg



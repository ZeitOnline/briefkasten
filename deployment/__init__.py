import sys
from os import path
import ConfigParser as ConfigParser_


class ConfigParser(ConfigParser_.SafeConfigParser):
    """ a ConfigParser that can provide its values as simple dictionary.
    taken from http://stackoverflow.com/questions/3220670/read-all-the-contents-in-ini-file-into-dictionary-with-python"""

    def as_dict(self):
        d = dict(self._sections)
        for k in d:
            d[k] = dict(self._defaults, **d[k])
            d[k].pop('__name__', None)
        return d


ALL_STEPS = ['bootstrap',
    'create-appserver',
    'configure-appserver',
    'update-appserver']


DEFAULT_CONFIG = dict(
    host=dict(
        os='freebsd',
        iface='em0',
        timeserver='time.euro.apple.com',
        timezone='Europe/Berlin',  # relative path to /usr/share/zoneinfo/
    ),
    appserver=dict(
        ip_addr='127.0.0.2',
        port=6543,
        app_user='pyramid',
        app_home='/usr/local/briefkasten/',
        root_url='/',
        ),
    webserver=dict(ip_addr='127.0.0.3'),
)


def usage():
    print """Usage:
    %s config-file [%s]

    performs the given deployment steps (or all if none are given) using the specified configuration
    """ % (sys.argv[0], ', '.join(ALL_STEPS))

# top level listing of what to upload for the application server
APP_SRC = [
    'briefkasten',
    'middleware_scripts',
    'appserver.cfg',
    'bootstrap.py',
    'briefkasten.ini.in',
    'setup.cfg',
    'setup.py',
]


def commandline():
    if len(sys.argv) < 2:
        usage()
        exit()

    # apply config file to default configuration
    parser = ConfigParser(allow_no_value=True)
    parser.read(sys.argv[1])
    parsed_dict = parser.as_dict()
    config = DEFAULT_CONFIG.copy()
    for key in parsed_dict.keys():
        if key in config:
            config[key].update(parsed_dict.get(key, dict()))
        else:
            config[key] = parsed_dict[key]
    # inject the absolute location of the config file so consumers can resolve relative paths
    config['fs_path'] = path.dirname(path.abspath(sys.argv[1]))
    # determine the host os (we only support -- and default to -- FreeBSD atm)
    host_os = config['host'].get('os', 'freebsd').lower()
    if host_os == 'freebsd':
        from freebsd import deploy
        deploy(config, steps=sys.argv[2:])
    else:
        print "%s is not supported as host operating system." % host_os

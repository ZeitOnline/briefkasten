import sys
import ConfigParser as ConfigParser_


class ConfigParser(ConfigParser_.ConfigParser):
    """ a ConfigParser that can provide is values as simple dictionary.
    taken from http://stackoverflow.com/questions/3220670/read-all-the-contents-in-ini-file-into-dictionary-with-python"""

    def as_dict(self):
        d = dict(self._sections)
        for k in d:
            d[k] = dict(self._defaults, **d[k])
            d[k].pop('__name__', None)
        return d


def usage():
    print """Usage:
    %s config-file
    """ % sys.argv[0]


def commandline():
    if len(sys.argv) != 2:
        usage()
        exit()
    parser = ConfigParser()
    parser.read(sys.argv[1])
    config = parser.as_dict()
    # determine the host os (we only support -- and default to -- FreeBSD atm)
    host_os = config['host'].get('os', 'freebsd').lower()
    if host_os == 'freebsd':
        from freebsd import deploy
        deploy(config)
    else:
        print "%s is not supported as host operating system." % host_os

import click
from os import path
from .dropbox import DropboxContainer


def get_settings(fs_config):
    import ConfigParser

    class MyParser(ConfigParser.SafeConfigParser):

        def as_dict(self):
            d = dict(self._sections)
            for k in d:
                d[k] = dict(self._defaults, **d[k])
                d[k].pop('__name__', None)
            return d

    parser = MyParser()
    parser.read(fs_config)
    return parser.as_dict()['app:briefkasten']


@click.command(help='Scans dropbox directory for unprocessed drops and processes them')
@click.option(
    '--config',
    '-c',
    default='development.ini',
    help='''location of the configuration file. Must be a .ini file with a section named 'app:briefkasten'.''')
@click.argument(
    'drop_id',
    required=False,
    default=None,
)
def main(config, drop_id=None):     # pragma: no cover
    settings = get_settings(path.abspath(config))
    drop_root = DropboxContainer(settings=settings)

    if drop_id is not None:
        drops = [drop_root.get_dropbox(drop_id)]
    else:
        drops = drop_root

    for drop in drops:
        print(drop)

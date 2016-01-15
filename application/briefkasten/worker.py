import click
from os import path
from .dropbox import DropboxContainer


def get_settings(fs_config):
    # for now we simply hardcode the settings
    # TODO: parse the actual .ini file
    return dict(
        fs_dropbox_root='var/drops/',
        fs_pgp_pubkeys='',
        editors=[],
        admins=[],
    )


@click.command(help='Scans dropbox directory for unprocessed drops and processes them')
@click.option(
    '--config',
    '-c',
    default='development.ini',
    help='location of the configuration file')
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

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
def main(config):     # pragma: no cover
    settings = get_settings(path.abspath(config))
    drop_root = DropboxContainer(settings=settings)

    for drop in drop_root:
        print(drop)

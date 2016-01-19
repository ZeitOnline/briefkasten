import click
from os import path
from multiprocessing import Pool
from watchdog.observers import Observer
from watchdog.events import FileSystemEventHandler
from threading import Condition

from .dropbox import DropboxContainer
from .notifications import setup_smtp_factory


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


class MyHandler(FileSystemEventHandler):

    def __init__(self, main_loop_cond):
        self.main_loop_cond = main_loop_cond

    def on_modified(self, event):
        self.main_loop_cond.acquire()
        self.main_loop_cond.notify()
        self.main_loop_cond.release()
        print "directory modified"


def run_watchdog():
    # once a day we should scan for old drop boxes
    # at noon we should test pgp keys
    pass


def process_drop(drop):
    drop.process()
    # todo: ensure it is in the right directory


@click.command(help='debug a single drop')
@click.option(
    '--root',
    '-r',
    default='var/drops/',
    help='''location of the dropbox container directory''')
@click.argument(
    'drop_id',
    required=False,
    default=None,
)
def debug(root, drop_id=None):     # pragma: no cover
    root = DropboxContainer(root=root)
    for drop in root:
        print(drop)


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
def main(config):     # pragma: no cover
    settings = get_settings(path.abspath(config))
    if 'smtp' not in settings:
        settings['smtp'] = setup_smtp_factory(**settings)
    drop_root = DropboxContainer(settings=settings)

    # Should point to the todo-directory, or drop dir
    fs_path = '.'

    workers = Pool(processes=settings.workers)

    condition = Condition()
    event_handler = MyHandler(condition)

    observer = Observer()
    observer.schedule(event_handler, fs_path, recursive=False)
    observer.start()

    condition.acquire()
    while True:
        for drop in drop_root:
            print(drop)
            if(drop.status_int == 200):
                workers.map_async(process_drop, [drop])

        # Wait for directory to change or timeout to occur
        if not condition.wait(43200):
            run_watchdog()

    condition.release()

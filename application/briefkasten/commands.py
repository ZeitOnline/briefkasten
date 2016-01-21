import click
from os import path, listdir, rename, remove
from sys import exit
from multiprocessing import Pool
from signal import signal, SIGINT
from watchdog.observers import Observer
from watchdog.events import FileSystemEventHandler
from threading import Condition

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


class MyHandler(FileSystemEventHandler):

    def __init__(self, main_loop_cond):
        self.main_loop_cond = main_loop_cond

    def on_modified(self, event):
        self.main_loop_cond.acquire()
        self.main_loop_cond.notify()
        self.main_loop_cond.release()


def keyboard_interrupt_handler(signal, frame):
    print 'Caught keyboard interrupt. Exit.'
    exit(0)

def run_watchdog():
    # once a day we should scan for old drop boxes
    # at noon we should test pgp keys
    # also: scan for and clean up watchdog entries
    pass


def process_drop(drop):
    try:
        rename(
            path.join(drop.container.fs_submission_queue, drop.drop_id),
            path.join(drop.container.fs_scratch, drop.drop_id)
        )
    except:
        return

    drop.process()

    # remove token from scratch dir, we're done
    remove(path.join(drop.container.fs_scratch, drop.drop_id))


@click.command(help='debug processing of drops')
@click.option(
    '--root',
    '-r',
    default='var/drop_root/',
    help='''location of the dropbox container directory''')
@click.argument(
    'drop_id',
    required=False,
    default=None,
)
def debug(root, drop_id=None):     # pragma: no cover
    drop_root = root = DropboxContainer(root=root)
    if drop_id is not None:
        drops = [drop_root.get_dropbox(drop_id)]
    else:
        drops = drop_root
    for drop in drops:
        print('debugging %s' % drop)
        if drop.status_int == 20:
            drop.process()


@click.command(help='Scans dropbox directory for unprocessed drops and processes them')
@click.option(
    '--root',
    '-r',
    default='var/drop_root/',
    help='''location of the dropbox container directory''')
@click.option(
    '--debug/--no-debug',
    default=False,
    help='''process synchronously, allowing to set break points etc.''')
def worker(root, debug=False):     # pragma: no cover
    drop_root = DropboxContainer(root=root)
    settings = drop_root.settings

    # Setup multiprocessing pool with that amount of workers as
    # implied by the amount of worker jails
    if not debug:
        workers = Pool(processes=settings.get('num_workers', 1))

    # Setup the condition object that we will wait for, it
    # signals changes in the directory
    condition = Condition()

    # Setup and run the actual file system event watcher
    event_handler = MyHandler(condition)
    observer = Observer()
    observer.schedule(event_handler, drop_root.fs_submission_queue, recursive=False)
    observer.start()

    signal(SIGINT, keyboard_interrupt_handler)

    # grab lock, scan submission dir for jobs and process them
    condition.acquire()
    while True:
        for drop_id in listdir(drop_root.fs_submission_queue):
            print(drop_id)
            drop = drop_root.get_dropbox(drop_id)

            # Only look at drops that actually are for us
            if drop.status_int == 20:
                # process drops without attachments synchronously
                if not debug and drop.num_attachments > 0:
                    workers.map_async(process_drop, [drop])
                else:
                    process_drop(drop)
            else:
                print('Not processing drop with status %d ' % drop.status_int)

        # Wait for directory content to change
        condition.wait()

    condition.release()

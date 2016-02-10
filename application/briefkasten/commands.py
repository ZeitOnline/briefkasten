import click
from os import path, listdir, rename, remove
from datetime import datetime
from sys import exit
from multiprocessing import Pool
from signal import signal, SIGINT
from watchdog.observers import Observer
from watchdog.events import FileSystemEventHandler
from threading import Condition

from .dropbox import DropboxContainer


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


@click.command(help='performs sanity and config checks and cleans up old drops')
@click.option(
    '--root',
    '-r',
    default='var/drop_root/',
    help='''location of the dropbox container directory''')
def janitor(root):     # pragma: no cover
    drop_root = root = DropboxContainer(root=root)

    # Scan pub keys for expired or soon to expired ones
    allkeys = root.gpg_context.list_keys()
    now = datetime.utcnow()
    report = ''

    for editor in drop_root.settings['editors']:
        key = [k for k in allkeys if editor in ', '.join(k['uids'])]
        if not bool(key):
            report = report + 'Editor %s does not have a public key in keyring.\n' % editor
            continue
        key = key[0]

        if not key.get('expires'):
            report = report + 'Editor %s has a key that never expires.\n' % editor
            continue

        keyexpiry = datetime.utcfromtimestamp(int(k['expires']))
        delta = keyexpiry - now

        if delta.days < 0:
            report = report + 'Editor %s has an expired key.\n' % editor
        elif delta.days < 60:
            report = report + 'Editor ' + editor + ' has a key that will expire in %d days.\n' % delta.days

    for drop in drop_root:
        print('debugging %s' % drop)
        age = now - drop.last_changed()
        if age.days > 365:
            print('drop %s is older than a year. Removing it.' % drop)
            drop.destroy()


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


@click.command(help='Scans dropbox submission directory for unprocessed drops and processes them')
@click.option(
    '--root',
    '-r',
    default='var/drop_root/',
    help='''location of the dropbox container directory''')
def debug_worker(root):     # pragma: no cover
    drop_root = DropboxContainer(root=root)

    while True:
        for drop_id in listdir(drop_root.fs_submission_queue):
            print(drop_id)
            drop = drop_root.get_dropbox(drop_id)

            # Only look at drops that actually are for us
            if drop.status_int == 20:
                process_drop(drop)
            else:
                print('Not processing drop %s with status %d ' % (drop.drop_id, drop.status_int))


@click.command(help='listens for changes to submission directory and processes them asynchronously')
@click.option(
    '--root',
    '-r',
    default='var/drop_root/',
    help='''location of the dropbox container directory''')
@click.option(
    '--async/--no-async',
    default=True,
    help='''process asynchronously''')
def worker(root, async=True):     # pragma: no cover
    drop_root = DropboxContainer(root=root)
    settings = drop_root.settings

    # Setup multiprocessing pool with that amount of workers as
    # implied by the amount of worker jails
    if async:
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
                if async and drop.num_attachments > 0:
                    workers.map_async(process_drop, [drop])
                else:
                    process_drop(drop)
            else:
                print('Not processing drop %s with status %d ' % (drop.drop_id, drop.status_int))

        # Wait for directory content to change
        condition.wait()

    condition.release()

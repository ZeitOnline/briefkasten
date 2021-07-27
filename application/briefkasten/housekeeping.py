import os
from datetime import datetime
from .dropbox import DropboxContainer


def gather_metrics(drop_root):
    # Scan pub keys for expired or soon to expired ones
    allkeys = drop_root.gpg_context.list_keys()
    now = datetime.utcnow()
    report = ''
    metrics = dict(pgp_key_expiry_unixtime=[])
    age = None
    for editor in drop_root.settings['editors']:
        key = [k for k in allkeys if editor in ', '.join(k['uids'])]
        if not bool(key):
            report = report + 'Editor %s does not have a public key in keyring.\n' % editor
            continue
        key = key[0]

        if not key.get('expires'):
            report = report + 'Editor %s has a key that never expires.\n' % editor
            continue

        keyexpiry = datetime.utcfromtimestamp(int(key['expires']))
        metrics['pgp_key_expiry_unixtime'].append(dict(timestamp=keyexpiry.timestamp(), email=editor))
        delta = keyexpiry - now

        if age is None or delta.seconds < age:
            age = delta.seconds
        if delta.days < 0:
            report = report + 'Editor %s has a key that expired %d days ago.\n' % (editor, abs(delta.days))
        elif delta.days < 60:
            report = report + 'Editor ' + editor + ' has a key that will expire in %d days.\n' % delta.days
    return report, metrics


def garbage_collection(drop_root):
    for drop in drop_root:
        age = datetime.utcnow() - drop.last_changed()
        max_age = 365 if not drop.from_watchdog else 1

        if age.days > max_age:
            if not drop.from_watchdog:
                print('drop %s is expired. Removing it.' % drop)
            drop.destroy()


def prometheus_metrics(**kw):
    """ returns the entirety of the exposed prometheus metrics
    """
    report = """
# HELP pgp_key_expiry_unixtime Expiry date in unix epoch seconds of the given PGP key
"""
    for expiry in kw['pgp_key_expiry_unixtime']:
        report += """pgp_key_expiry_unixtime{{user="{email}"}} {timestamp:.3f}\n""".format(**expiry)
    return report


def do(root):
    drop_root = DropboxContainer(root=root)
    report, metrics = gather_metrics(drop_root)
    garbage_collection(drop_root)
    # print humanreadable report for commandline warriors :)
    print(report)
    prometheus_report = prometheus_metrics(**metrics)
    with open(os.path.join(drop_root.fs_root, 'metrics'), 'w') as metrics_handle:
        metrics_handle.writelines(prometheus_report)

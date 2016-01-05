import smtplib
import gnupg

from email.mime.multipart import MIMEMultipart

# debug
from pprint import pprint
from cStringIO import StringIO as BIO

def checkRecipient(gpg_context, r):
    uid = '<' + r + '>'
    valid_keys = [ k for k in gpg_context.list_keys() if uid in ', '.join(k['uids']) and k['trust'] in 'ofqmu-' ]
#   pprint(valid_keys)
    return not not valid_keys

def sendMultiPart(sender, to, subject, attachments):
    msg = MIMEMultipart()

    msg['From'] = sender
    msg['To'] = to
    msg['Subject'] = subject

    for textfile in attachments:
        with open(textfile, 'rb') as fp:
            attach = MIMEText(fp.read())
            msg.attach(attach)

    s = smtplib.SMTP('localhost')
    s.sendmail(sender, to, msg.as_string())
    s.quit()

def process_main(
        dropbox,
        admins,
        editors,
        gnupghome='/Users/erdgeist/.gnupg',
        sender='donotreply@localhost',
        cleanser='',
        cleanser_ssh_conf='' ):

    gpg_context = gnupg.GPG(gnupghome=gnupghome)

    # create initial backup if we can't clean
    backup_recipients = [ r for r in editors + admins if checkRecipient(gpg_context, r) ]
    # print backup_recipients

    # this will be handled by watchdog, no need to send for each drop
    if not backup_recipients:
        dropbox.status = u'500 no valid keys at all'
        return

    file_out = BIO()
    with tarfile.open(mode = 'w|', fileobj = file_out) as tar:
        tar.add(dropbox.fs_path)
    gpg_context.encrypt(file_out.getvalue(), backup_recipients, always_trust=True, output=join(dropbox.fs_path, 'backup.tar.gpg') )




process_main( dropbox=object(), admins=[ 'erdgeist@erdgeist.org', 'tom@tomster.org' ], editors=[ 'atoth@ccc.de' ] )


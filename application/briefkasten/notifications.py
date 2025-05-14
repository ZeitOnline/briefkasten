from email.mime.multipart import MIMEMultipart
from email.mime.base import MIMEBase
from email.mime.text import MIMEText
from email.utils import formatdate
from os.path import basename


def checkRecipient(gpg_context, uid):
    valid_key = bool([k for k in gpg_context.list_keys() if uid in ', '.join(k['uids']) and k['trust'] in 'ofqmu-'])
    if not valid_key:
        print('Invalid recipient %s' % uid)
    return valid_key


def composeMessages(gpg_context, sender, recipients, subject, text, attachments):
    """ a helper method that composes an email with attachments """
    for to in recipients:
        if not to.startswith('<'):
            uid = '<%s>' % to
        else:
            uid = to

        if not checkRecipient(gpg_context, uid):
            continue

        msg = MIMEMultipart()

        msg['From'] = sender
        msg['To'] = to
        msg['Subject'] = subject
        msg["Date"] = formatdate(localtime=True)
        msg.preamble = u'This is an email in encrypted multipart format.'

        attach = MIMEText(str(gpg_context.encrypt(text.encode('utf-8'), uid, always_trust=True)))
        attach.set_charset('UTF-8')
        msg.attach(attach)

        for attachment in attachments:
            with open(attachment, 'rb') as fp:
                attach = MIMEBase('application', 'octet-stream')
                attach.set_payload(str(gpg_context.encrypt_file(fp, uid, always_trust=True)))
            attach.add_header('Content-Disposition', 'attachment', filename=basename('%s.pgp' % attachment))
            msg.attach(attach)

        yield msg

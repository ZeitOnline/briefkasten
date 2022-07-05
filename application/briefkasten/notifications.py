from email.mime.multipart import MIMEMultipart
from email.mime.base import MIMEBase
from email.mime.text import MIMEText
from email.utils import formatdate
from os.path import basename
from smtplib import SMTP


class CustomSMTP(SMTP):

    def __init__(self, *args, **kwargs):
        self.host = kwargs.pop('host', 'localhost')
        self.port = kwargs.pop('port', 25)
        self.user = kwargs.pop('user', '')
        self.password = kwargs.pop('password', '')
        SMTP.__init__(self, *args, **kwargs)

    def begin(self):
        """ connects and optionally authenticates a connection."""
        self.connect(self.host, self.port)
        self.helo()
        if self.user:
            self.starttls()
            self.login(self.user, self.password)


def setup_smtp_factory(**settings):
    """ expects a dictionary with 'mail.' keys to create an appropriate smtplib.SMTP instance"""
    return CustomSMTP(
        host=settings.get('mail.host', 'localhost'),
        port=int(settings.get('mail.port', 25)),
        user=settings.get('mail.user'),
        password=settings.get('mail.password'),
        timeout=float(settings.get('mail.timeout', 60)),
    )


def checkRecipient(gpg_context, uid):
    valid_key = bool([k for k in gpg_context.list_keys() if uid in ', '.join(k['uids']) and k['trust'] in 'ofqmu-'])
    if not valid_key:
        print('Invalid recipient %s' % uid)
    return valid_key


def sendMultiPart(smtp, gpg_context, sender, recipients, subject, text, attachments):
    """ a helper method that composes and sends an email with attachments
    requires a pre-configured smtplib.SMTP instance"""
    sent = 0
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

        # TODO: need to catch exception?
        # yes :-) we need to adjust the status accordingly (>500 so it will be destroyed)
        smtp.begin()
        smtp.sendmail(sender, to, msg.as_string())
        smtp.quit()
        sent += 1

    return sent

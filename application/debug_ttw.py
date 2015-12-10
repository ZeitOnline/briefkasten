from os import path
import click
import requests
from webtest.app import TestApp, AppError


@click.command()
@click.option(
    '--message',
    '-m',
    default=u'Hello there'
)
@click.option(
    'attachments',
    '-a',
    multiple=True
)
@click.argument(
    'url',
    default=u'http://localhost:6543',
)
def submit_attachment(url, message, attachments):
    click.echo('running against %s!' % url)
    # files = [('attachments', (attachment, open(path.abspath(attachment)))) for attachment in attachments]
    browser = TestApp(url)
    submit_page = browser.get('/briefkasten/')
    submit_form = submit_page.forms['briefkasten-form']
    submit_form['message'] = u'Hello there'
    try:
        response = submit_form.submit()
        import pdb; pdb.set_trace()
        click.echo(u'Got %s' % response.url)
    except AppError as exc:
        click.echo(u'Oops %s' % exc)

if __name__ == '__main__':
    submit_attachment()

# coding: utf-8
from fabric import api as fab
from bsdploy.fabutils import rsync

fab.env.shell = '/bin/sh -c'


@fab.task
def upload_packages():
    rsync('-av',
        'downloads/packages/',
        '{host_string}:/data/tomster/briefkasten-poudriere/')



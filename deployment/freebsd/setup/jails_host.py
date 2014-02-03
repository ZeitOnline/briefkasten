# coding: utf-8
from fabric import api as fab
from fabric.contrib.project import rsync_project
from mr.awsome.ezjail.fabric import bootstrap
from fabric_scripts import _git_base

fab.env.shell = '/bin/sh -c'


# shutup pyflakes
(bootstrap, )

def download_distfiles():
    pass


def upload_distfiles():
    pass

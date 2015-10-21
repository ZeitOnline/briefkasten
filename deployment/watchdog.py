# coding: utf-8
from os import path
from fabric import api as fab
from fabric.contrib.files import upload_template
from fabric.api import env
from ploy.config import value_asbool
from bsdploy.fabutils import rsync_project

env.shell = '/bin/sh -c'


ansible_vars = None

# hide stdout by default
from fabric.state import output
output['stdout'] = False

defaults = {
    'watchdog_max_process_secs': 60,
}


def get_vars():
    global ansible_vars
    if ansible_vars is None:
        print "fetching ansible vars"
        hostname = env.host_string.split('@')[-1]
        ansible_vars = dict(hostname=hostname, **defaults)
        ansible_vars.update(**env.instances[hostname].get_ansible_variables())


def install_watchdog(build=True):
    get_vars()
    app_dir = ansible_vars['watchdog_app_dir']
    app_user = ansible_vars['watchdog_app_user']

    with fab.lcd('../../../watchdog'):
        upload_template(
            filename='watchdog.ini.in',
            template_dir=path.abspath(path.join(path.dirname(__file__), '../../../watchdog')),
            destination='{watchdog_app_dir}/watchdog.ini'.format(**ansible_vars),
            context=ansible_vars,
            use_jinja=True,
            mode='444',
        )

        if value_asbool(build):
            fab.local('rm -rf dist')
            fab.local('../deployment/freebsd/bin/mkrelease -n')
        rsync_project(remote_dir=path.join(app_dir, 'upload/'),
            local_dir='dist/briefkasten_watchdog*.zip')
        rsync_project(remote_dir=path.join(ansible_vars['watchdog_app_dir'], 'upload/'),
            local_dir='requirements.txt')
        with fab.cd(app_dir):
            fab.sudo('bin/pip install -r upload/requirements.txt', user=app_user)
            fab.sudo('bin/pip install --force-reinstall --upgrade upload/briefkasten_watchdog*.zip', user=app_user)

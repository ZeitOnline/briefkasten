from os import path
from fabric import api as fab
from fabric.contrib.project import rsync_project
from fabric.contrib.files import upload_template
from ezjailremote import fabfile as ezjail
from ezjailremote.utils import jexec

from deployment import ALL_STEPS


def deploy(config, steps=[]):
    print "Deploying on FreeBSD."
    # by default, all steps are performed on the jailhost
    fab.env['host_string'] = config['host']['ip_addr']

    all_steps = {
        'bootstrap': (bootstrap, (config,)),
        'create-appserver': (create_appserver, (config,)),
        'configure-appserver': (jexec, (config['appserver']['ip_addr'], configure_appserver, config)),
        'update-appserver': (jexec, (config['appserver']['ip_addr'], update_appserver, config)),
        }

    for step in ALL_STEPS:
        if not steps or step in steps:
            funk, arx = all_steps[step]
            print step
            funk(*arx)


def bootstrap(config):
    # run ezjailremote's basic bootstrap
    ezjail.bootstrap(primary_ip=config['host']['ip_addr'])

    # configure IP addresses for the jails
    for jailhost in ['webserver', 'appserver']:
        alias = config[jailhost]['ip_addr']
        fab.sudo("""echo 'ifconfig_%s_alias="%s"' >> /etc/rc.conf""" % (config['host']['iface'], alias))
        fab.sudo("""ifconfig %s alias %s""" % (config['host']['iface'], alias))

    # set the time
    fab.sudo("cp /usr/share/zoneinfo/%s /etc/localtime" % config['host']['timezone'])
    fab.sudo("ntpdate %s" % config['host']['timeserver'])

    # configure crypto volume for jails
    fab.sudo("""gpart add -t freebsd-zfs -l jails -a8 %s""" % config['host']['root_device'])
    fab.puts("You will need to enter the passphrase for the crypto volume THREE times")
    fab.puts("Once to provide it for encrypting, a second time to confirm it and a third time to mount the volume")
    fab.sudo("""geli init gpt/jails""")
    fab.sudo("""geli attach gpt/jails""")
    fab.sudo("""zpool create jails gpt/jails.eli""")
    fab.sudo("""sudo zfs mount -a""")  # sometimes the newly created pool is not mounted automatically

    # install ezjail
    ezjail.install(source='cvs', jailzfs='jails/ezjail', p=True)


def create_appserver(config):
    ezjail.create('appserver',
        config['appserver']['ip_addr'], ctype='zfs')


def configure_appserver(config):
    # create application user
    app_user = config['appserver']['app_user']
    app_home = config['appserver']['app_home']
    fab.sudo("pw user add %s" % app_user)
    # upload port configuration
    local_resource_dir = path.join(path.abspath(path.dirname(__file__)))
    fab.sudo("mkdir -p /var/db/ports/")
    fab.put(path.join(local_resource_dir, 'appserver/var/db/ports/*'),
        "/var/db/ports/",
        use_sudo=True)
    # install ports
    for port in ['lang/python',
        'sysutils/py-supervisor',
        'net/rsync',
        'textproc/libxslt']:
        with fab.cd('/usr/ports/%s' % port):
            fab.sudo('make install')
    fab.sudo('mkdir -p %s' % app_home)
    fab.sudo('''echo 'supervisord_enable="YES"' >> /etc/rc.conf ''')
    # create custom buildout.cfg
    local_resource_dir = path.join(path.abspath(path.dirname(__file__)))
    # configure supervisor (make sure logging is off!)
    upload_template(filename=path.join(local_resource_dir, 'supervisord.conf.in'),
        context=dict(app_home=app_home, app_user=app_user),
        destination='/usr/local/etc/supervisord.conf',
        backup=False,
        use_sudo=True)
    config['appserver']['configure-hasrun'] = True


def update_appserver(config):
    configure_hasrun = config['appserver'].get('configure-hasrun', False)
    # upload sources
    import briefkasten
    from deployment import APP_SRC
    app_home = config['appserver']['app_home']
    app_user = config['appserver']['app_user']
    base_path = path.abspath(path.join(path.dirname(briefkasten.__file__), '..'))
    local_paths = ' '.join([path.join(base_path, app_path) for app_path in APP_SRC])
    fab.sudo('chown -R %s %s' % (fab.env['user'], app_home))
    rsync_project(app_home, local_paths, delete=True)
    # upload theme
    fs_remote_theme = path.join(app_home, 'themes')
    config['appserver']['fs_remote_theme'] = path.join(fs_remote_theme, path.split(config['appserver']['fs_theme_path'])[-1])
    fab.run('mkdir -p %s' % fs_remote_theme)
    rsync_project(fs_remote_theme,
        path.abspath(path.join(config['fs_path'], config['appserver']['fs_theme_path'])),
        delete=True)
    # create custom buildout.cfg
    local_resource_dir = path.join(path.abspath(path.dirname(__file__)))
    upload_template(filename=path.join(local_resource_dir, 'buildout.cfg.in'),
        context=config['appserver'],
        destination=path.join(app_home, 'buildout.cfg'),
        backup=False)

    fab.sudo('chown -R %s %s' % (app_user, app_home))
    # bootstrap and run buildout
    with fab.cd(app_home):
        fab.sudo('python2.7 bootstrap.py', user=app_user)
        fab.sudo('bin/buildout', user=app_user)
    # start supervisor
    if configure_hasrun:
        fab.sudo('/usr/local/etc/rc.d/supervisord start')
    else:
        fab.sudo('supervisorctl restart briefkasten')


def create_webserver(config):
    ezjail.create('webserver',
        config['webserver']['ip_addr'], ctype='zfs')


def configure_webserver(config):
    # upload site root
    # install nginx via ports
    # create or upload pem
    # configure nginx
    # start nginx
    pass

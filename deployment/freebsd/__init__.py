from os import path
from shutil import rmtree
from tempfile import mkdtemp
from OpenSSL import crypto
from fabric import api as fab
from fabric.contrib.project import rsync_project
from fabric.contrib.files import upload_template
from ezjailremote import fabfile as ezjail
from ezjailremote.api import BaseJail

from deployment import ALL_STEPS


def deploy(config, steps=[]):
    print "Deploying on FreeBSD."
    # by default, all steps are performed on the jailhost
    fab.env['host_string'] = config['host']['ip_addr']

    # TODO: step execution should be moved up to general deployment,
    # it's not OS specific (actually, it should move to ezjail-remote eventually)

    webserver = WebserverJail(**config['webserver'])
    webserver.app_config = config['appserver']

    all_steps = {
        'bootstrap': (bootstrap, (config,)),
        'create-appserver': (create_appserver, (config,)),
        'configure-appserver': (configure_appserver, (config,)),
        'update-appserver': (update_appserver, (config,)),
        'create-webserver': (webserver.create, ()),
        'configure-webserver': (webserver.configure, ()),
        'update-webserver': (webserver.update, ()),
        }

    for step in ALL_STEPS:
        if not steps or step in steps:
            funk, arx = all_steps[step]
            print step
            funk(*arx)


def bootstrap(config):
    # run ezjailremote's basic bootstrap
    orig_user = fab.env['user']
    host_ip = config['host']['ip_addr']
    ezjail.bootstrap(primary_ip=host_ip)
    fab.env['user'] = orig_user

    # configure IP addresses for the jails
    fab.sudo("""echo 'cloned_interfaces="lo1"' >> /etc.rc.conf""")
    fab.sudo("""echo 'ipv4_addrs_lo1="127.0.0.2-10/32"' >> /etc.rc.conf""")
    fab.sudo('ifconfig lo1 create')
    for ip in range(2, 11):
        fab.sudo('ifconfig lo1 alias 127.0.0.%s' % ip)
    for jailhost in ['webserver', 'appserver']:
        alias = config[jailhost]['ip_addr']
        if alias != host_ip and not alias.startswith('127.0.0.'):
            fab.sudo("""echo 'ifconfig_%s_alias="%s"' >> /etc/rc.conf""" % (config['host']['iface'], alias))
            fab.sudo("""ifconfig %s alias %s""" % (config['host']['iface'], alias))

    # set up NAT for the jails
    fab.sudo("""echo 'nat on %s from 127.0/24 to any -> %s' > /etc/pf.conf""" % (config['host']['iface'], host_ip))
    fab.sudo("""echo 'pf_enable="YES"' >> /etc/rc.conf""")
    fab.sudo("""/etc/rc.d/pf start""")
    # TODO: should deactivate net access for the jails after they've built their packages?

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
    ezjail.install(source='cvs', jailzfs='%s/ezjail' % config['host']['zpool'], p=True)


def create_appserver(config):
    ezjail.create('appserver',
        config['appserver']['ip_addr'])


def configure_appserver(config):
    # create application user
    app_user = config['appserver']['app_user']
    app_home = config['appserver']['app_home']
    jail_root = '/usr/jails/appserver'
    fab.sudo("pw user add %s -V %s/etc -b %s/home/" % (app_user, jail_root, jail_root))
    # upload port configuration
    local_resource_dir = path.join(path.abspath(path.dirname(__file__)))
    fab.sudo("mkdir -p %s/var/db/ports/" % jail_root)
    fab.put(path.join(local_resource_dir, 'appserver/var/db/ports/*'),
        "%s/var/db/ports/" % jail_root,
        use_sudo=True)
    # install ports
    for port in ['lang/python',
        'sysutils/py-supervisor',
        'net/rsync',
        'textproc/libxslt']:
        fab.sudo("""ezjail-admin console -e 'make -C /usr/ports/%s install' appserver""" % port)
    fab.sudo('mkdir -p %s' % path.join(jail_root, app_home))
    fab.sudo('''echo 'supervisord_enable="YES"' >> %s/etc/rc.conf ''' % jail_root)
    local_resource_dir = path.join(path.abspath(path.dirname(__file__)))
    # configure supervisor (make sure logging is off!)
    upload_template(filename=path.join(local_resource_dir, 'supervisord.conf.in'),
        context=dict(app_home=app_home, app_user=app_user),
        destination='%s/usr/local/etc/supervisord.conf' % jail_root,
        backup=False,
        use_sudo=True)
    config['appserver']['configure-hasrun'] = True


def update_appserver(config):
    configure_hasrun = config['appserver'].get('configure-hasrun', False)
    # upload sources
    import briefkasten
    from deployment import APP_SRC
    jail_root = '/usr/jails/appserver'
    app_home = config['appserver']['app_home']
    app_user = config['appserver']['app_user']
    userinfo = fab.sudo('pw usershow -V %s/etc -n %s' % (jail_root, app_user))
    numeric_app_user = userinfo.split(':')[3]
    base_path = path.abspath(path.join(path.dirname(briefkasten.__file__), '..'))
    local_paths = ' '.join([path.join(base_path, app_path) for app_path in APP_SRC])

    # upload project
    fab.sudo("""mkdir -p %s%s""" % (jail_root, app_home))
    fab.sudo('chown -R %s %s%s' % (fab.env['user'], jail_root, app_home))
    rsync_project('%s%s' % (jail_root, app_home), local_paths, delete=True)

    # upload theme
    fs_remote_theme = path.join(app_home, 'themes')
    config['appserver']['fs_remote_theme'] = path.join(fs_remote_theme, path.split(config['appserver']['fs_theme_path'])[-1])
    fab.run('mkdir -p %s%s' % (jail_root, fs_remote_theme))
    rsync_project('%s%s' % (jail_root, fs_remote_theme),
        path.abspath(path.join(config['fs_path'], config['appserver']['fs_theme_path'])),
        delete=True)

    # create custom buildout.cfg
    local_resource_dir = path.join(path.abspath(path.dirname(__file__)))
    upload_template(filename=path.join(local_resource_dir, 'buildout.cfg.in'),
        context=config['appserver'],
        destination=path.join('%s%s' % (jail_root, app_home), 'buildout.cfg'),
        backup=False)

    fab.sudo('chown -R %s %s%s' % (numeric_app_user, jail_root, app_home))

    # bootstrap and run buildout
    if configure_hasrun:
        fab.sudo('''ezjail-admin console -e "sudo -u %s python2.7 %s/bootstrap.py -c %s/buildout.cfg"  appserver'''
            % (app_user, app_home, app_home))
        fab.sudo('''ezjail-admin console -e "sudo -u %s %s/bin/buildout -c %s/buildout.cfg"  appserver'''
            % (app_user, app_home, app_home))
    # start supervisor
    if configure_hasrun:
        fab.sudo('''ezjail-admin console -e "/usr/local/etc/rc.d/supervisord start" appserver''')
    else:
        fab.sudo('''ezjail-admin console -e "supervisorctl restart briefkasten" appserver''')


class WebserverJail(BaseJail):

    name = "webserver"
    ctype = 'zfs'
    sshd = False
    ports_to_install = ['www/nginx', ]

    def extra_configure(self):
        # enable nginx
        fab.sudo('''echo 'nginx_enable="YES"' >> %s/etc/rc.conf ''' % self.fs_remote_root)
        # create or upload pem
        tempdir = None

        # if no files were given, create an ad-hoc certificate and key
        if not (path.exists(self.cert_file)
            or path.exists(self.key_file)):

            tempdir = mkdtemp()
            cert_file = path.join(tempdir, 'briefkasten.crt')
            key_file = path.join(tempdir, 'briefkasten.key')

            # create a key pair
            # based on http://skippylovesmalorie.wordpress.com/2010/02/12/how-to-generate-a-self-signed-certificate-using-pyopenssl/
            pkey = crypto.PKey()
            pkey.generate_key(crypto.TYPE_RSA, 1024)

            # create a minimal self-signed cert
            cert = crypto.X509()
            cert.get_subject().CN = self.fqdn
            cert.set_serial_number(1000)
            cert.gmtime_adj_notBefore(0)
            cert.gmtime_adj_notAfter(365 * 24 * 60 * 60)
            cert.set_issuer(cert.get_subject())
            cert.set_pubkey(pkey)
            cert.sign(pkey, 'sha1')
            open(cert_file, "wt").write(
                crypto.dump_certificate(crypto.FILETYPE_PEM, cert))
            open(key_file, "wt").write(
                crypto.dump_privatekey(crypto.FILETYPE_PEM, pkey))

        fab.put(cert_file, '%s/usr/local/etc/nginx/briefkasten.crt' % self.fs_remote_root, use_sudo=True)
        fab.put(key_file, '%s/usr/local/etc/nginx/briefkasten.key' % self.fs_remote_root, use_sudo=True)
        if tempdir:
            rmtree(tempdir)

    def update(self):
        local_resource_dir = path.join(path.abspath(path.dirname(__file__)))
        # configure nginx (make sure logging is off!)
        upload_template(filename=path.join(local_resource_dir, 'nginx.conf.in'),
            context=dict(
                fqdn=self.fqdn,
                app_ip=self.app_config['ip_addr'],
                app_port=self.app_config['port'],
                wwwuser=self.wwwuser),
            destination='%s/usr/local/etc/nginx/nginx.conf' % self.fs_remote_root,
            backup=False,
            use_sudo=True)
        # start nginx
        if self.configurehasrun:
            self.console('/usr/local/etc/rc.d/nginx start')
        else:
            self.console('/usr/local/etc/rc.d/nginx reload')

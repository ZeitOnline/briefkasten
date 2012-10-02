from os import path
from shutil import rmtree
from tempfile import mkdtemp
from OpenSSL import crypto
from fabric import api as fab
from fabric.contrib.project import rsync_project
from fabric.contrib.files import exists as fabexists
from fabric.contrib.files import upload_template
from ezjailremote import fabfile as ezjail
from ezjailremote.api import BaseJail

from deployment import ALL_STEPS


def deploy(config, steps=[]):
    print "Deploying on FreeBSD."
    fab.env['host_string'] = config['host']['ip_addr']
    # TODO: step execution should be moved up to general deployment,
    # it's not OS specific (actually, it should move to ezjail-remote eventually)

    jailhost = BootstrapHost(config)
    appserver = AppserverJail(**config['appserver'])
    appserver.config_fs_path = config['fs_path']
    webserver = WebserverJail(**config['webserver'])
    webserver.app_config = config['appserver']

    all_steps = {
        'bootstrap': jailhost.bootstrap,
        'create-appserver': appserver.create,
        'configure-appserver': appserver.configure,
        'update-appserver': appserver.update,
        'create-webserver': webserver.create,
        'configure-webserver': webserver.configure,
        'update-webserver': webserver.update,
        }

    for step in ALL_STEPS:
        if not steps or step in steps:
            all_steps[step]()
            print step


class BootstrapHost(object):

    def __init__(self, config):
        self.config = config

    def bootstrap(self):
        config = self.config
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


class AppserverJail(BaseJail):

    name = "appserver"
    ctype = 'zfs'
    sshd = False
    ports_to_install = ['lang/python',
        'sysutils/py-supervisor',
        'net/rsync',
        'textproc/libxslt']

    def configure(self):
        # create application user
        with fab.settings(fab.show("output"), warn_only=True):
            self.console("pw user add %s" % self.app_user)
            fab.sudo('mkdir -p %s' % path.join(self.fs_remote_root, self.app_home))
        fab.sudo('''echo 'supervisord_enable="YES"' >> %s/etc/rc.conf ''' % self.fs_remote_root)
        local_resource_dir = path.join(path.abspath(path.dirname(__file__)))
        # configure supervisor (make sure logging is off!)
        upload_template(filename=path.join(local_resource_dir, 'supervisord.conf.in'),
            context=dict(app_home=self.app_home, app_user=self.app_user),
            destination='%s/usr/local/etc/supervisord.conf' % self.fs_remote_root,
            backup=False,
            use_sudo=True)

    def update(self):
        # upload sources
        import briefkasten
        from deployment import APP_SRC
        userinfo = fab.sudo('pw usershow -V %s/etc -n %s' % (self.fs_remote_root, self.app_user))
        numeric_app_user = userinfo.split(':')[3]
        base_path = path.abspath(path.join(path.dirname(briefkasten.__file__), '..'))
        local_paths = ' '.join([path.join(base_path, app_path) for app_path in APP_SRC])

        # upload project
        fab.sudo("""mkdir -p %s%s""" % (self.fs_remote_root, self.app_home))
        fab.sudo('chown -R %s %s%s' % (fab.env['user'], self.fs_remote_root, self.app_home))
        rsync_project('%s%s' % (self.fs_remote_root, self.app_home), local_paths, delete=True)

        # upload theme
        fs_remote_theme = path.join(self.app_home, 'themes')
        self.fs_remote_theme = fs_remote_theme = path.join(fs_remote_theme, path.split(self.fs_theme_path)[-1])
        fab.run('mkdir -p %s%s' % (self.fs_remote_root, fs_remote_theme))
        rsync_project('%s%s/' % (self.fs_remote_root, fs_remote_theme),
            '%s/' % path.abspath(path.join(self.config_fs_path, self.fs_theme_path)),
            delete=True)

        # create custom buildout.cfg
        local_resource_dir = path.join(path.abspath(path.dirname(__file__)))
        upload_template(filename=path.join(local_resource_dir, 'buildout.cfg.in'),
            context=self.__dict__,
            destination=path.join('%s%s' % (self.fs_remote_root, self.app_home), 'buildout.cfg'),
            backup=False)

        fab.sudo('chown -R %s %s%s' % (numeric_app_user, self.fs_remote_root, self.app_home))

        # bootstrap and run buildout
        if self.configurehasrun or not fabexists('%s%s/bin/buildout' % (self.fs_remote_root, self.app_home)):
            self.console('sudo -u %s python2.7 %s/bootstrap.py -c %s/buildout.cfg'
                % (self.app_user, self.app_home, self.app_home))
            self.console('sudo -u %s %s/bin/buildout -c %s/buildout.cfg'
                % (self.app_user, self.app_home, self.app_home))
        # start supervisor
        if self.configurehasrun:
            self.console('/usr/local/etc/rc.d/supervisord start')
        else:
            self.console('supervisorctl restart briefkasten')


class WebserverJail(BaseJail):

    name = "webserver"
    ctype = 'zfs'
    sshd = False
    ports_to_install = ['www/nginx', ]

    def configure(self):
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

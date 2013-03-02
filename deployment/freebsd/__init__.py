from os import path
from shutil import rmtree
from tempfile import mkdtemp
from OpenSSL import crypto
from fabric import api as fab
from fabric.context_managers import prefix
from fabric.contrib.project import rsync_project
from fabric.contrib.files import exists as fabexists
from fabric.contrib.files import upload_template
from ezjailremote import fabfile as ezjail
from ezjaildeploy import api


class JailHost(api.JailHost):

    iface = 'em0'
    root_device = 'ada0'
    timeserver = 'time.euro.apple.com'
    timezone = 'Europe/Berlin'  # relative path to /usr/share/zoneinfo
    jailzfs = 'jails/ezjail'
    install_from = 'cvs'

    def bootstrap(self):
        config = self.config
        # run ezjailremote's basic bootstrap

        with prefix("export PACKAGESITE=\'ftp://ftp.freebsd.org/pub/FreeBSD/ports/amd64/packages-9-stable/Latest/\'"):
            ezjail.bootstrap(primary_ip=self.ip_addr)
            fab.sudo('pkg_add -r rsync')

        # configure IP addresses for the jails
        fab.sudo("""echo 'cloned_interfaces="lo1"' >> /etc.rc.conf""")
        fab.sudo("""echo 'ipv4_addrs_lo1="127.0.0.2-10/32"' >> /etc.rc.conf""")
        fab.sudo('ifconfig lo1 create')
        for ip in range(2, 11):
            fab.sudo('ifconfig lo1 alias 127.0.0.%s' % ip)
        for jailhost in ['webserver', 'appserver']:
            try:
                alias = config[jailhost].get('ip_addr', self.available_blueprints[jailhost].ip_addr)
            except AttributeError:
                exit("You must provide an IP Address for the %s jail" % jailhost)
            if alias != self.ip_addr and not alias.startswith('127.0.0.'):
                fab.sudo("""echo 'ifconfig_%s_alias="%s"' >> /etc/rc.conf""" % (config['host'].get('iface', self.iface), alias))
                fab.sudo("""ifconfig %s alias %s""" % (config['host'].get('iface', self.iface), alias))

        # set up NAT for the jails
        fab.sudo("""echo 'nat on %s from 127.0/24 to any -> %s' > /etc/pf.conf""" % (config['host'].get('iface', self.iface), self.ip_addr))
        fab.sudo("""echo 'pf_enable="YES"' >> /etc/rc.conf""")
        fab.sudo("""/etc/rc.d/pf start""")
        # TODO: should deactivate net access for the jails after they've built their packages?

        # set the time
        fab.sudo("cp /usr/share/zoneinfo/%s /etc/localtime" % config['host'].get('timezone', self.timezone))
        fab.sudo("ntpdate %s" % config['host'].get('timeserver', self.timeserver))

        # configure crypto volume for jails
        label = self.jailzfs.split('/')[0]
        fab.sudo("""gpart add -t freebsd-zfs -l %s -a8 %s""" % (label, config['host'].get('root_device', self.root_device)))
        fab.puts("You will need to enter the passphrase for the crypto volume THREE times")
        fab.puts("Once to provide it for encrypting, a second time to confirm it and a third time to mount the volume")
        fab.sudo("""geli init gpt/%s""" % label)
        fab.sudo("""geli attach gpt/%s""" % label)
        fab.sudo("""zpool create %s gpt/%s.eli""" % (label, label))
        fab.sudo("""sudo zfs mount -a""")  # sometimes the newly created pool is not mounted automatically


class AppserverJail(api.BaseJail):

    ctype = 'zfs'
    sshd = False
    ip_addr = '127.0.0.2'
    port = 6543
    app_user = 'pyramid'
    app_home = '/usr/local/briefkasten/'
    root_url = '/'
    ports_to_install = ['lang/python27',
        'sysutils/py-supervisor',
        'net/rsync',
        'textproc/libxslt',
        'security/sudo']

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
        logdir = '''mkdir -p %s%s/var/log/''' % (self.fs_remote_root, self.app_home)
        fab.sudo('''mkdir -p logdir''' % logdir)

    def update(self):
        # upload sources
        import deployment
        userinfo = fab.sudo('pw usershow -V %s/etc -n %s' % (self.fs_remote_root, self.app_user))
        numeric_app_user = userinfo.split(':')[3]
        base_path = path.abspath(path.join(path.dirname(deployment.__file__), '..'))
        local_paths = ' '.join([path.join(base_path, app_path) for app_path in deployment.APP_SRC])

        # upload project
        fab.sudo("""mkdir -p %s%s""" % (self.fs_remote_root, self.app_home))
        fab.sudo('chown -R %s %s%s' % (fab.env['user'], self.fs_remote_root, self.app_home))
        rsync_project('%s%s' % (self.fs_remote_root, self.app_home), local_paths, delete=True)
        # HACK: remove watchdog.py to avoid its dependencies
        # during pyramid scan (it should really be a separate
        # package altogether)
        fab.sudo('rm %s%s/briefkasten/watchdog.py' % (self.fs_remote_root, self.app_home))

        # upload theme
        fs_remote_theme = path.join(self.app_home, 'themes')
        self.fs_remote_theme = fs_remote_theme = path.join(fs_remote_theme, path.split(self.fs_theme_path)[-1])
        fab.run('mkdir -p %s%s' % (self.fs_remote_root, fs_remote_theme))

        rsync_project('%s%s/' % (self.fs_remote_root, fs_remote_theme),
            '%s/' % path.abspath(path.join(self.jailhost.config['_fs_config'], self.fs_theme_path)),
            delete=True)

        # create custom buildout.cfg
        local_resource_dir = path.join(path.abspath(path.dirname(__file__)))
        upload_template(filename=path.join(local_resource_dir, 'buildout.cfg.in'),
            context=self.__dict__,
            destination=path.join('%s%s' % (self.fs_remote_root, self.app_home), 'buildout.cfg'),
            backup=False)

        # finally, give ownership of the application directory to the application user
        fab.sudo('chown -R %s %s%s' % (numeric_app_user, self.fs_remote_root, self.app_home))

        # bootstrap and run buildout
        if not fabexists('%s%s/bin/buildout' % (self.fs_remote_root, self.app_home)):
            self.console('sudo -u %s python2.7 %s/bootstrap.py  --version=1.6.3 -c %s/buildout.cfg'
                % (self.app_user, self.app_home, self.app_home))
        self.console('sudo -u %s %s/bin/buildout -c %s/buildout.cfg'
            % (self.app_user, self.app_home, self.app_home))
        # start supervisor
        with fab.settings(fab.show("output"), warn_only=True):
            if self.preparehasrun:
                self.console('/usr/local/etc/rc.d/supervisord start')
            else:
                restarted = self.console('supervisorctl restart briefkasten')
                if 'no such file' in restarted:
                    self.console('/usr/local/etc/rc.d/supervisord start')


class WebserverJail(api.BaseJail):

    ctype = 'zfs'
    sshd = False
    ports_to_install = ['www/nginx', ]
    fqdn = 'briefkasten.local'
    wwwuser = 'www'
    cert_file = None
    key_file = None

    def configure(self):
        # enable nginx
        fab.sudo('''echo 'nginx_enable="YES"' >> %s/etc/rc.conf ''' % self.fs_remote_root)
        # create or upload pem
        tempdir = None

        # if no files were given, create an ad-hoc certificate and key
        if self.cert_file is None or self.key_file is None or not (path.exists(self.cert_file)
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
        appserver = self.jailhost.jails['appserver']
        upload_template(filename=path.join(local_resource_dir, 'nginx.conf.in'),
            context=dict(
                fqdn=self.fqdn,
                app_ip=appserver.ip_addr,
                app_port=appserver.port,
                wwwuser=self.wwwuser),
            destination='%s/usr/local/etc/nginx/nginx.conf' % self.fs_remote_root,
            backup=False,
            use_sudo=True)
        # start nginx
        with fab.settings(fab.show("output"), warn_only=True):
            if self.preparehasrun:
                self.console('/usr/local/etc/rc.d/nginx start')
            else:
                reloaded = self.console('/usr/local/etc/rc.d/nginx reload')
                if 'nginx not running' in reloaded:
                    self.console('/usr/local/etc/rc.d/nginx start')


class CleanserJail(api.BaseJail):

    ctype = 'zfs'
    sshd = True
    ip_addr = '127.0.0.3'
    ports_to_install = [
        'graphics/netpbm',
        'print/ghostscript9',
        'editors/libreoffice',
        'archivers/zip',
    ]

from fabric import api as fab
from ezjailremote import fabfile as ezjail
from ezjailremote.utils import jexec


def deploy(config):
    print "Deploying on FreeBSD."
    fab.env['host_string'] = config['host']['ip_addr']
    bootstrap(config)
    create_appserver(config)


def bootstrap(config):
    ezjail.bootstrap(primary_ip=config['host']['ip_addr'])

    # configure IP addresses for the jails
    for jailhost in ['webserver', 'appserver']:
        alias = config[jailhost]['ip_addr']
        fab.sudo("""echo 'ifconfig_%s_alias="%s"' >> /etc/rc.conf""" % (config['host']['iface'], alias))
        fab.sudo("""ifconfig %s alias %s""" % (config['host']['iface'], alias))

    # configure crypto volume for jails
    fab.sudo("""gpart add -t freebsd-zfs -l jails -a8 %s""" % config['host']['root_device'])
    fab.puts("You will need to enter the passphrase for the crypto volume THREE times")
    fab.puts("Once to provide it for encrypting, a second time to confirm it and a third time to mount the volume")
    fab.sudo("""geli init gpt/jails""")
    fab.sudo("""geli attach gpt/jails""")
    fab.sudo("""zpool create jails gpt/jails.eli""")
    fab.sudo("""sudo zfs mount -a""")  # sometimes the newly created pool is not mounted automatically

    # install ezjail
    ezjail.install(source='cvs', jailzfs='jails/ezjail')


def create_appserver(config):
    ezjail.create('appserver',
        config['appserver']['ip_addr'], ctype='zfs')

    def configure_appserver():
        # TODO install more dependencies to run pyramid
        fab.sudo('pkg_add -r python27')

    jexec(config['appserver']['ip_addr'], configure_appserver)

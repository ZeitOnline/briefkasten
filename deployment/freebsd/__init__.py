from fabric import api as fab
from ezjailremote import fabfile as ezjail
from ezjailremote.utils import jexec


def deploy(config):
    print "Deploying on FreeBSD."
    fab.env['host_string'] = config['host']['ip_addr']
    bootstrap(config)
    create_appserver(config)
    jexec(config['appserver']['ip_addr'], configure_appserver, config)
    create_webserver(config)
    jexec(config['webserver']['ip_addr'], configure_webserver, config)


def bootstrap(config):
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
    # upload site root
    # install ports
    # * lang/python27
    # * sysutils/py-supervisor
    # upload sources
    # bootstrap and run buildout
    # configure supervisor
    # start supervisor
    pass


def create_webserver(config):
    ezjail.create('webserver',
        config['webserver']['ip_addr'], ctype='zfs')


def configure_webserver():
    # upload site root
    # install nginx via ports
    # create or upload pem
    # configure nginx
    # start nginx
    pass

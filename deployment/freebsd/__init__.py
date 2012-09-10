from fabric import api as fab


def deploy(config):
    print "Deploying on FreeBSD."
    bootstrap(config)
    appserver(config)


def bootstrap(config):
    pass


def appserver(config):
    fab.env['host_string'] = config['host']['ip_addr']
    from ezjailremote import fabfile
    fabfile.create('appserver',
        config['appserver']['ip_addr'], ctype='zfs')

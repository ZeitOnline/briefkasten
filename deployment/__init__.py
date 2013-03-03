# top level listing of what to upload for the application server
APP_SRC = [
    'briefkasten',
    'middleware_scripts',
    'appserver.cfg',
    'bootstrap.py',
    'briefkasten.ini.in',
    'setup.cfg',
    'setup.py',
]

def deploy_freebsd():
    from deployment import freebsd
    from ezjaildeploy.commandline import main
    main(blueprints=freebsd)

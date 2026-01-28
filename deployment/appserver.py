from os import path
from fabric import api as fab
from fabric.api import env, task
from bsdploy.fabutils import rsync
from ploy.config import value_asbool

AV = None

# hide stdout by default
# from fabric.state import output
# output['stdout'] = False


def get_vars():
    global AV
    if AV is None:
        hostname = env.host_string.split("@")[-1]
        AV = dict(hostname=hostname, **env.instances[hostname].get_ansible_variables())
    return AV


@task
def upload_theme():
    """ upload and/or update the theme with the current git state"""
    get_vars()
    with fab.settings():
        local_theme_path = path.abspath(
            path.join(
                fab.env["config_base"], fab.env.instance.config["local_theme_path"]
            )
        )
        rsync(
            "-av",
            "--delete",
            f"{local_theme_path}/",
            "{{host_string}}:{themes_dir}/{ploy_theme_name}".format(**AV),
        )
        briefkasten_ctl("restart")


@task
def upload_pgp_keys():
    """ upload and/or update the PGP keys for editors, import them into PGP"""
    get_vars()
    upload_target = "/tmp/pgp_pubkeys.tmp"
    with fab.settings(fab.hide("running")):
        fab.run(f"rm -rf {upload_target}")
        fab.run(f"mkdir {upload_target}")
        local_key_path = path.join(
            fab.env["config_base"], fab.env.instance.config["local_pgpkey_path"]
        )
        remote_key_path = "/var/briefkasten/pgp_pubkeys/".format(**AV)
        rsync("-av", local_key_path, f"{{host_string}}:{upload_target}")
        fab.run("chown -R {} {}".format(AV["appuser"], remote_key_path))
        fab.run(f"chmod 700 {remote_key_path}")
        with fab.shell_env(GNUPGHOME=remote_key_path):
            # gpg is stingy with exit code 0:
            with fab.warn_only():
                fab.sudo(
                    f"""gpg --import {upload_target}/*.*""",
                    user=AV["appuser"],
                    shell_escape=False,
                )
        fab.run(f"rm -rf {upload_target}")


@task
def upload_backend(index="dev", user=None):
    """
    Build the backend and upload it to the remote server at the given index
    """
    get_vars()
    use_devpi(index=index)
    with fab.lcd("../application"):
        fab.local("make upload")


@task
def briefkasten_ctl(action="restart"):
    get_vars()
    what = env.host_string.split("-")[-1]
    if what == "appserver":
        what = "frontend"
    fab.sudo(
        "supervisorctl {action} briefkasten_{what}".format(
            action=action, what=what, **AV
        ),
        warn_only=True,
    )


@task
def update_backend(use_pypi=False, index="dev", build=True, user=None, version=None):
    """
    Install the backend from the given devpi index at the given version on the target host
    and restart the service.

    If version is None, it defaults to the latest version

    Optionally, build and upload the application first from local sources. This requires a
    full backend development environment on the machine running this command (pyramid etc.)
    """
    get_vars()
    if value_asbool(build):
        upload_backend(index=index, user=user)
    with fab.cd("{apphome}".format(**AV)):
        if value_asbool(use_pypi):
            command = "bin/pip install --upgrade %s"
        else:
            command = (
                f"bin/pip install --upgrade --pre -i "
                f"{AV['ploy_default_publish_devpi']}/briefkasten/{index}/+simple/ %s"
            )
        if version:
            app_command = f"{command}=={version}"
        else:
            app_command = command
        fab.sudo(app_command % 'briefkasten')
        theme_package = AV.get('ploy_theme_package')
        if theme_package is not None and theme_package != 'briefkasten':
            theme_command = command % theme_package
            fab.sudo(theme_command)

    briefkasten_ctl("restart")


@task
def use_devpi(index="dev"):
    get_vars()
    publish_devpi = AV.get("ploy_default_publish_devpi")
    return fab.local(
        f"devpi use {publish_devpi}/briefkasten/{index}",
        capture=True,
    )


@task
def login_devpi(index="dev", user=None):
    use_devpi(index=index)
    if user is None:
        user = fab.env["user"]
    fab.local(f"devpi login {user}")

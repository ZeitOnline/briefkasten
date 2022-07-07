# Two mandatory tasks before build image:
# 1. Copy the /briefkasten folder briefkasten-config repository.
#    The build process with `make` includes `pip install` which requires
#    the Pipfile under `/briefkasten/watchdog/Pipfile`
#
# 2. Copy your ssh folder like `~/.ssh .ssh`
FROM ubuntu:20.04
RUN apt-get update
RUN apt-get install -y python2 make tox python-crypto python-dev openssh-client build-essential
WORKDIR /briefkasten
CMD ["bash"]

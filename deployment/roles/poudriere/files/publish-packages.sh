#!/bin/sh
rsync -av --delete /usr/local/poudriere/data/packages/111amd64-briefkasten-briefkasten/ briefkastenpkg.zeit.de:/usr/jails/webserver/var/www/data/briefkastenpkg/11.1/
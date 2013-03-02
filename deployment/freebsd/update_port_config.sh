#!/bin/sh

for jail in webserver appserver cleanser

do
    rsync -av $1:/usr/jails/$jail/var/db/ports/* $jail/var/db/ports/
done
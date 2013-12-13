#!/bin/sh

# define our bail out shortcut
exerr () { echo "ERROR: $*" >&2 ; exit 1; }

[ $# -lt 1 ] && exerr "Syntax: $0 uid"

the_keys=`gpg --quiet --list-pub --with-colons $1 2>/dev/null | grep ^pub:[ofqmu-]:`
exit $?

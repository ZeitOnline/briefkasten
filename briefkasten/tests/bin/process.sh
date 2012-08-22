#!/bin/sh

exerr () { echo "ERROR: $*" >&2 ; exit 1; }

# parse commands
while getopts :d:c: arg; do case ${arg} in
  c) the_config="${OPTARG}";;
  d) the_dropdir="${OPTARG}";;
  ?) exerr $usage;;
esac; done; shift $(( ${OPTIND} - 1 ))

echo $the_dropdir
[ -d "$the_dropdir" ] || exerr "Can't access drop directory"

exit 0
#!/bin/sh

# this mocked script always returns success and simply moves the dirty
# attachments untouched into the clean directory - what a lazy bum!
#
# process-attachments.sh -d dropdir
#

# define our bail out shortcut
exerr () { echo "ERROR: $*" >&2 ; exit 1; }
exnerr() { printf "%s %s\n" $1 $2 > "${the_dropdir}"/status; exit 1; }

: ${MOCKED_STATUS_CODE:=299}

# this is the usage string in case of error
usage="process-attachments.sh [-d dropdir] [-c config]"

# parse commands
while getopts :d:c: arg; do case ${arg} in
  d) the_dropdir="${OPTARG}";;
  c) the_config="${OPTARG}";;
  ?) exerr $usage;;
esac; done; shift $(( ${OPTIND} - 1 ))

[ -d "${the_dropdir}" ] || exnerr 501 "Can't access drop directory"

# Check for attachment directory.
# If it is not there, we got nothing to do
[ -d "${the_dropdir}"/attach/ ] || exit 0

case ${MOCKED_STATUS_CODE} in
    299)
        mv "${the_dropdir}"/attach "${the_dropdir}"/clean
        mkdir "${the_dropdir}"/attach
        printf "299 Cleansed" > "${the_dropdir}"/status
        exit 0
        ;;
    800)
        mv "${the_dropdir}"/attach "${the_dropdir}"/clean
        mkdir "${the_dropdir}"/attach
        printf "800 At least one uncleansed" > "${the_dropdir}"/status
        exit 0
        ;;
    540)
        printf "540 Error while cleaning" > "${the_dropdir}"/status
        exit 1
        ;;
    *)
        printf "%s Generic mocked code" ${MOCKED_STATUS_CODE} > "${the_dropdir}"/status
        exit 1
        ;;
esac

exit 0

#!/bin/sh
# Author of this script is Dirk Engling <erdgeist@erdgeist.org>
# It is in the public domain.
#
# process-attachments.sh -d dropdir
#
# This script parses through all the attachments and tries to
# unpack archives it finds on the way.
#
# For all the known files it finds it calls the cleaning function
# it knows about
#
###################################

# some defaults, user configurable

###
# Do not edit anything below this line
###

##
# function declarations
process_single_file () {
  the_file=$1
  the_destination=$2

  # First determine the file type
  the_type=`file -bi "${the_file}"`

  case ${the_type%;*} in
  text/plain)          cp                "${the_file}" "${the_destination}";;
  text/html)           process-html.sh   "${the_file}" "${the_destination}";;
  application/msword)  process-msword.sh "${the_file}" "${the_destination}";;
  application/pdf)     process-pdf.sh    "${the_file}" "${the_destination}";;
  audio/mpeg)          process-mpeg.sh   "${the_file}" "${the_destination}";;
  image/*)             process-image.sh  "${the_file}" "${the_destination}" "${the_type}";;

# archive and compression format
  application/zip)     process_zip.sh    "${the_file}" "${the_destination}";;
  application/x-bzip2) process_bzip.sh   "${the_file}" "${the_destination}";;
  application/x-tar)   process_tar.sh    "${the_file}" "${the_destination}";;

# every unknown format is just copied
# this means that the server tried its best and is at least not worse
# than plain email
  *)                   cp                "${the_file}" "${the_destination}";;

  esac
}

# define our bail out shortcut
exerr () { echo "ERROR: $*" >&2 ; exit 1; }
exnerr() { printf "%s %s\n" $1 $2 > "${the_dropdir}"/status; exit 1; }

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

# If we're passed a config file to parse, source it
[ "${the_config}" -a -r "${the_config}" ] && . "${the_config}"

unset my_dispatcher
if [ "${the_jdispatcher_dir}" ]; then

  # Try to grab a cleanser
  # This normally should not fail, because there's
  # never more workers than jails. So wait, only then fail.
  unset retries
  while [ -z "${my_dispatcher}" -a "${#retries}" -lt 3 ]; do
    retries=${retries}X
    my_dispatcher=$( "${the_jdispatcher_dir}"/claim )
    if [ $? -ne 0 ]; then
      unset my_dispatcher
      sleep 10
    fi
  done

  # If we can not allocate a dispatcher here, return an error
  # TODO: report, what went wrong, maybe wait
  [ "${my_dispatcher}" ] || exnerr 502 "No remote cleanser available"

  read cleanser_ippport < "${my_dispatcher}"/ip
  [ "${cleanser_ippport}" ] || exnerr 503 "Cleanser config error"

  # Setup cleanser ip and port
  the_cleanser=${cleanser_ippport%%:*}
  the_ssh_conf="-o Port=${cleanser_ippport##*:} -o User=cleanser"

  # If we were asked to use jdispatch but can not deduct how
  # to connect, return an error
  [ "${the_cleanser}" ] || exnerr 503 "Cleanser config error"

  printf "201 Acquired remote cleanser: %s\n\nCopying data.\n" "${the_cleanser}" > "${the_dropdir}"/status
fi

# If we have a remote cleanser host, clean the attachments there
if [ "${the_cleanser}" ]; then
  the_ssh_conf="${the_ssh_conf} -o PasswordAuthentication=no"
  [ "${the_cleanser_ssh_conf}" ] && the_ssh_conf="-F ${the_cleanser_ssh_conf} ${the_ssh_conf}"
  the_remote_dir=`basename "${the_dropdir}"`

  [ "${my_dispatcher}" ] || printf "202 Using static remote cleanser: %s.\n\nCopying data.\n" "${the_cleanser}" > "${the_dropdir}"/status

  # copy over the attachments
  scp ${the_ssh_conf} -r ${the_dropdir} ${the_cleanser}:${the_remote_dir}
  [ $? -eq 0 ] || exnerr 504 "Could not copy dropdir to cleanser."

  printf "203 Attachments being processed by actual cleanser\n" > "${the_dropdir}"/status

  # execute remote cleanser job
  ssh ${the_ssh_conf} ${the_cleanser} process-attachments.sh -d ${the_remote_dir}
  the_return_code=$?

  # get back the result (and error code in status file)
  scp ${the_ssh_conf} -r ${the_cleanser}:${the_remote_dir} `dirname ${the_dropdir}`
  [ $? -eq 0 ] || exnerr 505 "Could not copy back dropdir from cleanser."

  # remove remote dir or release jail to jdispatcher
  if [ "${my_dispatcher}" ]; then
    # If the jail has been wiped from the outside, we assume a timeout
    [ -f "${my_dispatcher}"/token/taken ] || exnerr 520 "cleanser timeout failure."

    ${my_dispatcher}/release
  else
    # ignore errors
    ssh ${the_ssh_conf} ${the_cleanser} rm -r "${the_remote_dir}"
  fi

  # leave status file as reported by cleanser
  exit ${the_return_code}
fi

# this is the recursion path, when this script is being run on the remote
# host, usually without the config parameter.
printf "204 Attachments in quarantine on actual cleanser host.\n" > "${the_dropdir}"/status

mkdir "${the_dropdir}"/clean
for the_attachment in "${the_dropdir}"/attach/*; do
  [ -f "${the_attachment}" ] && process_single_file "${the_attachment}" ${the_dropdir}/clean
done

exit 0

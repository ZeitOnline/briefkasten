#!/bin/sh
# Author of this script is Dirk Engling <erdgeist@erdgeist.org>
# It is in the public domain.
#
# process.sh -d dropdir
#
# This is the overall process script glueing together everything
# that should happen to a drop once all the files from webserver
# have been written.
#
# Anything the donator wrote in the HTML form should reside in
# dropdir/message, all uploads in dropdir/attach
#
#
#
###################################

# some defaults, user configurable
: ${the_default_message="/usr/local/etc/briefkasten/default_message"}

###
# Do not edit anything below this line
###

RM=`which srm`
[ -z "${RM}" ] && RM=`which rm`

# define our bail out shortcut
exerr () { echo "ERROR: $*" >&2 ; exit 1; }
exnerr() { printf "%s %s" $1 $2 > "${the_dropdir}"/status; exit 1; }

case `uname -s` in
  Darwin)  the_sendmail_bin="/usr/sbin/sendmail";;
  FreeBSD) the_sendmail_bin="/usr/sbin/sendmail";;
  Linux)   the_sendmail_bin="/usr/lib/sendmail";;
  *) echo "Can't deduct your operating system, exiting" >&2; exit 1;;
esac

test_pgp() {
  gpg --quiet --list-pub --with-colons "<$1>" 2>/dev/null | grep -q ^pub:[ofqmu-]:
}

# this is the usage string in case of error
usage="process.sh [-c config] [-d dropdir]"

# parse commands
while getopts :d:c: arg; do case ${arg} in
  c) the_config="${OPTARG}";;
  d) the_dropdir="${OPTARG}";;
  ?) exerr $usage;;
esac; done; shift $(( ${OPTIND} - 1 ))

# Import user config
: ${the_config="/usr/local/etc/briefkasten.conf"}
[ -f "${the_config}" ] && . "${the_config}"
[ -d "${the_dropdir}" ] || exerr "Can't access drop directory"

# Create a primary encrypted backup of the drop.
# This can be re-evaluated if anything below fails
# The file is encrypted to the editors and the admins
the_backup_recipients=
for the_recipient in ${the_editors} ${the_admins}; do
  test_pgp ${the_recipient} && the_backup_recipients="${the_backup_recipients} -r ${the_recipient}"
done

# If we have no valid pgp keys at all, bail out
# This is very bad, since we do not have a way to inform
# the adminstrator.
# XXX maybe send an unencrypted email. Get feedback on this
[ -n "${the_backup_recipients}" ] || exerr "None of the admins or editors has a valid public key"

# Our initial sanity checks are done. Set status to 100
printf "100 Processor running.\n" > "${the_dropdir}"/status

# Archive and encrypt
tar cf - ${the_dropdir} | gpg -e ${the_backup_recipients} -o "${the_dropdir}/backup.tar.gpg" --trust-model always 2>/dev/null || exnerr 501 "Can't encrypt primary backup"

# If there is no message from user, make one up
[ -r "${the_dropdir}/message" ] || cp ${the_default_message} ${the_dropdir}/message

# Clean all attachments and move cleaned versions to the clean/ directory
export the_config
if ! process-attachments.sh -d "${the_dropdir}"; then
  # If processing the attachments failed, we assume that process-attachments.sh
  # has set the status. Clean up and return the error to web app
  ${RM} -rf ${the_dropdir}/message ${the_dropdir}/attach ${the_dropdir}/clean ${the_dropdir}/backup.tar.gpg
  exit 1
fi

# All went fine, send mails to the editors
unset out fail
for the_editor in ${the_editors}; do

  # Collect all attachments
  find ${the_dropdir}/clean/ -type f | \
  create-multipart.sh -f "${the_sender}" -t "${the_editor}" -s "Drop ID `basename ${the_dropdir}`" -p ${the_dropdir}/message > ${the_dropdir}/mail.eml 2> ${the_dropdir}/report

  if [ $? = 0 ]; then
    ${the_sendmail_bin} -t ${the_sender} < ${the_dropdir}/mail.eml
    out=X${out}
  else
    for the_admin in ${the_admins}; do
      echo -n | create-multipart.sh -f ${the_sender} -t ${the_admin} -s "FAILURE: Drop ID `basename ${the_dropdir}`" -p ${the_dropdir}/report | ${the_sendmail_bin} -t ${the_sender}  2> /dev/null
    done
    fail=X${fail}
  fi

  ${RM} -f ${the_dropdir}/mail.eml
done

# We're done with the drop if at least one recipient could be encrypted to
# wipe it
${RM} -rf ${the_dropdir}/message ${the_dropdir}/attach ${the_dropdir}/clean ${the_dropdir}/backup.tar.gpg

# if at least one message has been sent, we consider it "not a failure"
if [ "${out}" -a "${fail}" ]; then
  printf "901 Success. %s encrypted emails sent, %d failed.\n\nThe administrators have been notified.\n" ${#out} ${#fail} > "${the_dropdir}"/status
elif [ "${out}" ]; then
  printf "900 Success. %s encrypted emails sent.\n" ${#out} > "${the_dropdir}"/status
else
  printf "500 Failure. Sending to all %s editors failed.\n" ${#fail} > "${the_dropdir}"/status
  exit 1
fi

# Create directory for editor's replies
mkdir -p ${the_dropdir}/replies

# Return success code
exit 0

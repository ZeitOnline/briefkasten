#!/bin/sh

# Fix the path so this script also works from cron
PATH="${PATH}":/bin:/sbin:/usr/bin:/usr/sbin:/usr/local/bin:/usr/local/sbin

# Warn 14 days before expiry
the_now=`date +%s`
the_expirywarndate=$(( ${the_now} + 14 * 60 * 60 * 24 ))

case `uname -s` in
  Darwin)  the_sendmail_bin="/usr/sbin/sendmail";;
  FreeBSD) the_sendmail_bin="/usr/sbin/sendmail";;
  Linux)   the_sendmail_bin="/usr/lib/sendmail";;
  *) echo "Can't deduct your operating system, exiting" >&2; exit 1;;
esac

# define our bail out shortcut
exerr () { echo "ERROR: $*" >&2 ; exit 1; }

# Send an unencrypted email to the admins
report_error() {
  ( echo "Subject: Briefkasten status report for admin at `date`"
    echo Date: `date +"%a, %d %b %Y %T %z"`
    echo
    echo "$*" ) | ${the_sendmail_bin} -t ${the_sender} ${the_admins}
  exit 1
}

# Send an encrypted email to the admin
report_error_gpg() {
 for the_admin in ${the_admins}; do
   the_report=`mktemp /tmp/report_XXXXXXX`
   the_failreport=`mktemp /tmp/report_XXXXXXX`
   echo "$*" > ${the_report}
   echo -n | ${the_midware}/create-multipart.sh -f ${the_sender} -t ${the_admin} -s "Report for briefkasten daily script" -p ${the_report} > ${the_failreport} 2>/dev/null
   ${the_sendmail_bin} -t ${the_sender} < ${the_failreport}
   rm -f ${the_report} ${the_failreport}
 done
}

# Send an unencrypted email to the user $1 about time to expiry $2
report_error_user_expires() {
  the_user=$1
  the_expiry=$2
  the_days=$(( ( $2 - ${the_now} ) / ( 60 * 60 * 24 ) ))
  if [ ${the_days} -eq 0 ]; then
    the_days="heute"
  elif [ ${the_days} -eq 1 ]; then
    the_days="einen Tag"
  else
    the_days="${the_days} Tage"
  fi

  ( echo "Subject: WARNUNG: Ihr PGP-Key auf dem briefkasten ist nur noch ${the_days} gueltig"
    echo "To: $the_user"
    echo Date: `date +"%a, %d %b %Y %T %z"`
    echo
    echo Die Administratoren werden sich demnaechst darum kuemmern.
  ) | ${the_sendmail_bin} -t ${the_sender} ${the_user}
}

# Check for proper parameters
[ $# -eq 2 ] || exerr "Syntax: $0 <webappdir> <pgpdir>"
the_webappdir="$1"
the_midware="${the_webappdir}/middleware_scripts"
the_gpgdir="$2"

# Check if webapp directory exists
[ -d "${the_webappdir}" ] || exerr "webapp-dir ${the_webappdir} not found."

# Check for briefkasten configuration
[ -f "${the_midware}/briefkasten.conf" ] || exerr "briefkasten.conf expected at ${the_midware}/briefkasten.conf"

# Parse briefkasten configuration
. "${the_midware}/briefkasten.conf"

# Check for at least one admin to report to
[ -n "${the_admins}" ] || exerr "No admin to report to configured in ${the_midware}/briefkasten.conf."

#
# From now we do at least have an admin to send the email to
#

# Check for accessibility of gpg directory
[ -d "${the_gpgdir}" ] || report_error "gpg directory not found."
[ -r "${the_gpgdir}/pubring.gpg" ] || report_error "gpg directory not readable for this user."
export GNUPGHOME="${the_gpgdir}"

unset the_failadmins the_faileditors
for the_admin in ${the_admins}; do
  the_keys=`gpg --quiet --list-pub --with-colons ${the_admin} 2>/dev/null | grep ^pub:[ofqmu-]:`
  [ $? -eq 0 ] || the_failadmins="${the_failadmins} ${the_admin}"
done

for the_editor in ${the_editors}; do
  the_keys=`gpg --quiet --list-pub --with-colons ${the_editor} 2>/dev/null | grep ^pub:[ofqmu-]:`
  [ $? -eq 0 ] || the_faileditors="${the_faileditors} ${the_editor}"
done

# Check for keys that expire soon
unset the_failexpirytest the_expiredsoonkeys
for the_key in ${the_editors} ${the_admins}; do
  the_expiry=`gpg --quiet --list-pub --with-colons --fixed-list-mode ${the_key} 2>/dev/null | grep ^pub:[ofqmu-]: | cut -d : -f 7`
  if [ $? -ne 0 ]; then
    the_failexpirytest="${the_failexpirytest} ${the_key}"
  else
    if [ -z "${the_expiry}" ]; then
      the_neverexpires="${the_neverexpires} ${the_key}"
    elif [ ${the_expiry} -lt ${the_expirywarndate} ]; then
      the_expiredsoonkeys="${the_expiredsoonkeys} ${the_key}"
      report_error_user_expires ${the_key} ${the_expiry}
    fi
  fi
done

report_error_gpg "FAILADMIN: ${the_failadmins}\nFAILEDITOR: ${the_faileditors}\nFAILEXPIRYTEST: ${the_failexpirytest}\nEXPIREDSOON:${the_expiredsoonkeys}\nNEVEREXPIRES:${the_neverexpires}"

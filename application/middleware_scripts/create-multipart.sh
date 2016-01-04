#!/bin/sh
# Author of this script is Dirk Engling <erdgeist@erdgeist.org>
# It is in the public domain.
#
# create-multipart.sh -f from -t to -s subject -p messagetext FILE...
#
# This script creates a ready-to-be-sent multipart MIME message
# encrypting the message body and zero or more attachments to the
# recipient given on the command line.
#
# It uses gpg to encrypt message and attachments so the recipients
# key should exist in the keychain.
#
# You can send the E-Mail by piping this script's output through
# sendmail -t SENDERNAME
#
###################################

# some defaults, user configurable

: ${the_sender="noreply@briefkasten.zeit.de"}
: ${the_subject="encrypted message"}

###
# Do not edit anything below this line
###

# define our bail out shortcut
exerr () { echo "ERROR: $*" >&2 ; exit 1; }

# find a working base64 encoder
# invent a multipart separator
# cover slight differences in OS
base64_freebsd () { uuencode -m foo | tail -n +2 | sed -n '$!p'; }
case `uname -s` in
  Darwin)  encode_base64="base64 -b 72";
           the_boundary=`date | md5` ;;
  Linux)   encode_base64="base64 -w 72";
           the_boundary=`date | md5sum`;;
  FreeBSD) encode_base64="base64_freebsd";
           the_boundary=`date | md5`;;
  *) echo "Can't deduct your operating system, exiting" >&2; exit 1;;
esac

# this is the usage string in case of error
usage="create-multipart.sh [-f from] -t to [-s subject] -p message-file < the_attachments_list"

# parse commands
while getopts :f:t:s:p: arg; do case ${arg} in
  t) the_recipient="${OPTARG}";;
  f) the_sender="${OPTARG}";;
  s) the_subject="${OPTARG}";;
  p) the_message="${OPTARG}";;
  ?) exerr $usage;;
esac; done; shift $(( ${OPTIND} - 1 ))

[ -n "${the_recipient}" ] || exerr "No recipient specified"
[ -n "${the_message}" ] || exerr "No message file specified"

# ensure that we have a public key
gpg --quiet --list-pub --with-colons "<${the_recipient}>" 2>/dev/null | grep -q ^pub:[ofqmu-]: || exerr "No public key available for ${the_recipient}"

# start composing the email
echo "From: ${the_sender}"
echo "Reply-To: ${the_sender}"
echo "To: ${the_recipient}"
echo "Subject: ${the_subject}"
echo "Mime-Version: 1.0"
echo "Content-Type: multipart/mixed;"
echo " boundary=\"${the_boundary}\""
echo "X-Mailer: briefkasten"
echo
echo "This is a MIME multipart mail message."
echo
echo "--${the_boundary}"

echo "Content-Type: text/plain; charset=\"UTF-8\""
echo "Content-Transfer-Encoding: 8bit"
echo

# encrypt mail body
# the trust model is useless here, if the server is compromised, this won't be of any help
gpg -aer "${the_recipient}" -o - --trust-model always "${the_message}" 2>/dev/null || exerr "Can't encrypt message"

# for each attachment
while read the_attachment; do
  the_outname=`basename "${the_attachment}"`

  echo
  echo "--${the_boundary}"

  echo "Content-Type: application/octet-stream;"
  echo " name=\"${the_outname}.pgp\""
  echo "Content-Transfer-Encoding: base64"
  echo "Content-Disposition: attachment;"
  echo " filename=\"${the_outname}.pgp\""
  echo

  # encrypt and encode the attachment
  # the trust model is useless here, if the server is compromised, this won't be of any help
  gpg -er ${the_recipient} -o - --trust-model always "${the_attachment}" 2>/dev/null | ${encode_base64} || exerr "Can't encrypt attachment"

done

echo "--${the_boundary}--"

# Mail is complete

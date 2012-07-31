#!/bin/sh
# Author of this script is Dirk Engling <erdgeist@erdgeist.org>
# It is in the public domain.
#
# process-pdf.sh the_pdf the_destdir
#
# This script tries to remove all metadata from pdf files passed
# to it. It puts a resulting pdf to the destination directory.
#
###################################

# some defaults, user configurable

###
# Do not edit anything below this line
###

RM=`which srm`
[ -z "${RM}" ] && RM=`which rm`

# define our bail out shortcut
exerr () { echo "ERROR: $*" >&2 ; exit 1; }

# this is the usage string in case of error
usage="process-file.sh pdf_file destdir"

[ $# = 2 ] || exerr ${usage}

the_pdf="$1"
the_destdir="$2"

the_destpdf="${the_destdir}/`basename "${the_pdf}"`"
the_tempps="`dirname "${the_pdf}"`/pdf_tmpXXXXXXXX"
the_tempps=`mktemp "${the_tempps}"`

pdf2ps "${the_pdf}" "${the_tempps}"
ps2pdf "${the_tempps}" "${the_destpdf}"
${RM} -f "${the_tempps}"

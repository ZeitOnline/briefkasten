#!/bin/sh
# Author of this script is Dirk Engling <erdgeist@erdgeist.org>
# It is in the public domain.
#
# process-msword.sh the_msoffice_doc the_destdir
#
# This script converts the MS office document to a pdf in the
# destination directory, thus removing MS meta data.
#
# TODO: Filter it once more through our pdf->ps->pdf processor
#
###################################

# some defaults, user configurable

###
# Do not edit anything below this line
###

# define our bail out shortcut
exerr () { echo "ERROR: $*" >&2 ; exit 1; }

# this is the usage string in case of error
usage="process-msword.sh msoffice_doc destdir"

[ $# = 2 ] || exerr ${usage}

the_doc="$1"
the_destdir="$2"

libreoffice --headless --convert-to pdf:writer_pdf_Export --outdir "${the_destdir}" "${the_doc}"

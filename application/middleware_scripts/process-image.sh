#!/bin/sh
# Author of this script is Dirk Engling <erdgeist@erdgeist.org>
# It is in the public domain.
#
# process-image.sh the_image the_destdir the_mimetype
#
# This script tries to remove all metadata from image files passed
# to it. It puts a resulting image to the destination directory.
#
###################################

# some defaults, user configurable

###
# Do not edit anything below this line
###

# define our bail out shortcut
exerr () { echo "ERROR: $*" >&2 ; exit 1; }

# this is the usage string in case of error
usage="process-image.sh image destdir mimetype"

[ $# = 3 ] || exerr ${usage}

the_image=$1
the_destdir=$2
the_type=$3
unset the_back_converter

# Set default converter to png
# Set default outname to input name
the_destimage="${the_destdir}/`basename ${the_image}`"

case ${the_type} in
  image/jpeg\;*) the_back_converter=pnmtojpeg;;
  image/gif\;*) the_back_converter=ppmtogif;;
  image/png\;*) the_back_converter=pnmtopng;;
  image/bmp\;*) the_back_converter=ppmtobmp;;
  *)         the_back_converter=pnmtopng;
             the_destimage="${the_destdir}/`basename ${the_image}`.png";;
esac

# For all image formats containing only one image, we just convert the image
# to ppm and back. This drops all metadata in the file.
anytopnm ${the_image} | ${the_back_converter} > ${the_destimage}

# From animated images we generate a movie

# In an image there's more data that can give away the source, be it watermarks
# put in by the application, yellow dots on printed paper or CCD noise typical
# to a camera. We will try to remove at least the latter two and attach the images
# prepared that way to the editor for release.
#
# The process reduces the image's quality, so we won't make it default unless
# requested so in config

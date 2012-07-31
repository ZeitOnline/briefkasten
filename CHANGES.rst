0.1.3 - Unreleased
------------------

 * use a `cryptographically suitable random generator <http://docs.python.org/library/os.html#os.urandom>`_
   This addresses `issue #2 <https://github.com/ZeitOnline/briefkasten/issues/2>`_ 
   thanks to @alech (Alexander Klink) for reporting this.

 * use a `constant time comparison algorithm <http://codahale.com/a-lesson-in-timing-attacks/>`_ to avoid
   `timing attacks <https://en.wikipedia.org/wiki/Timing_attack>_.
   This addresses `issue #4 <https://github.com/ZeitOnline/briefkasten/issues/4>`_
   thanks to @stefanw (Stefan Wehrmeyer) for reporting this.

 * generate random filenames when saving uploaded attachments.
   this is both because their names may contain compromising information but also this could otherwise
   lead to files outside the dropbox container being overwritten.
   Thanks to Alexander Klink (@alech) for pointing out this flaw.

 * Use secure rm instead of rm, if it is available.

0.1.2 - 2010-07-31
------------------

 * further cosmetic layout fixes to the upload form
 * enable submission of up to ten attachments

0.1.1 - 2010-07-31
------------------

 * apply header and footer to the submission form (since it is no longer included via an iframe).

0.1 - 2010-07-30
----------------

Initial public release

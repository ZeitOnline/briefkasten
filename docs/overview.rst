ZEIT Online Briefkasten
-----------------------

The ``briefkasten`` (German for letterbox) is a reasonably secure web application for submitting content anonymously.

It allows to upload attachments which are then sanitized of a number of meta-data which could compromise the submitters identity. Next, the sanitized files are encrypted via GPG and sent via email to a pre-configured list of recipients. The original (potentially 'dirty') files are then deleted from the file system of the server. Thus, neither should admins with access to the server be able to access any submissions, nor should any of the recipients have access to the unsanitized raw material.

Upon successful upload the submitter receives a unique URL with a token that he or she can use to access any replies the recipients may post. That reply is the only data persisted on the server.

The implementation doesn't just contain the application itself but includes a complete deployment setup following what we believe to be best practices so that anybody should be able to host their own secure ``briefkasten`` with minimal setup pain.

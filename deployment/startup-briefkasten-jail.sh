#!/bin/sh
exec 1>/var/log/startup.log 2>&1
chmod 0600 /var/log/startup.log
set -e
set -x
env PACKAGESITE='https://briefkastenpkg.zeit.de/11.1/' SSL_CA_CERT_FILE=/etc/ssl/briefkastenpkg.zeit.de.pem pkg bootstrap
pkg update
pkg install python2

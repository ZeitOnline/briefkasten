#!/bin/sh
exec 1>/var/log/startup.log 2>&1
chmod 0600 /var/log/startup.log
set -e
set -x
ASSUME_ALWAYS_YES=yes
export ASSUME_ALWAYS_YES
pkg bootstrap
pkg update
pkg install python3

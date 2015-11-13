#!/bin/sh

# For ezjail's zfs
. /usr/local/etc/ezjail.conf
: ${ezjail_jaildir="/usr/jails"}

the_dispatch_script="/usr/home/erdgeist/jdispatch.sh"

# TODO: source our own config
# debug: set variables
the_worker_jails="cleanser1 cleanser2 cleanser3 cleanser4"
the_master_jail="appserver"
the_dispatchdir_prefix="${ezjail_jaildir}/${the_master_jail}"
the_dispatchdir_suffix="/var/run/jdispatch"
the_dispatchdir="${the_dispatchdir_prefix%/}/${the_dispatchdir_suffix#/}"
the_dispatch_lock="/var/lock/jdispatch.lock"
the_worker_snapshot=jdispatch_rollback
the_worker_timeout=180
the_proctitle="jdispatch_$( printf ${the_dispatchdir_prefix} | /sbin/sha512 | /usr/bin/head -c 16 )"


# define our bail out shortcut
exerr () { printf "Error: %s\n" "$*" >&2 ; /bin/rm -f "${the_dispatch_lock}"; exit 1; }

# Implementation
main() {
  now=$( date +%s )
  timeout=$(( now - the_worker_timeout ))

  # if there already is a lock, look how old it is.
  # Ancient locks will be killed (still a tiny race condition
  # after we remove it when another instance did so as well and
  # just now created their new lock)
  if [ -e "${the_dispatch_lock}" ]; then
    birthtime=$( /usr/bin/stat -f %B "${the_dispatch_lock}" )
    [ "${birthtime}" -lt "${timeout}" ] && /bin/rm -f "${the_dispatch_lock}"
  fi

  # Try to acquire lock (we might have been called from cron and jaildaemon simultaneously)
  unset retries
  while /bin/true; do
    [ ${#retries} -gt 3 ] && exerr "Can't acquire lock."
    if ! /usr/bin/mktemp "${the_dispatch_lock}" > /dev/null 2> /dev/null ; then
      retries=X${retries}
      sleep 5
      continue
    fi
  done

  # Check if our working environment exists
  [ -d "${the_dispatchdir_prefix}" ] || exerr "Error: dispatch dir ${the_dispatchdir_prefix} does not exist."

  # Create dispatch directory, if it does not exist
  /bin/mkdir -p "${the_dispatchdir}" || exerr "Error: Can not create dispatch directory ${the_dispatchdir}."
  if [ ! -f "${the_dispatchdir}/claim" ]; then
    printf "#!/bin/sh\nall_workers=\$( /bin/ls %s/*/claim | sort -R )\n" "${the_dispatchdir_suffix}" > "${the_dispatchdir}/claim"
    cat <<- 'EOF' >> "${the_dispatchdir}/claim"
      for worker in ${all_workers}; do
        [ -x "${worker}" ] && /bin/sh "${worker}" && echo $( dirname "${worker}" ) && exit 0
      done
      exit 1
EOF
  chmod 0755 "${the_dispatchdir}/claim"
  fi

  # Reap timeout and done workers
  for worker in ${the_worker_jails}; do
    unset cleanup

    # Extract IP address and port from worker configs
    worker_ipport="${worker##*,}"
    [ "${worker}" = "${worker_ipport}" ] && unset worker_ipport
    worker="${worker%%,*}"

    # generate rest of the worker configs
    worker_dir="${the_dispatchdir}"/"${worker}"
    worker_suffix="${the_dispatchdir_suffix}"/"${worker}"
    worker_snap="${ezjail_jailzfs}/${worker}@${the_worker_snapshot}"

    # For us to work on a worker jail, it needs to exit (ezjail needs to know about it) and
    # its zfs must have a snapshot
    if ! does_ezjail_exist ${worker}; then
      printf "Warning: Skipping jail %s. It does not exist.\n" "${worker}"
      continue
    fi

    if ! does_snapshot_exist ${worker_snap}; then
      printf "Warning: Skipping jail %s. Can not rollback, because No snapshot %s found on the zfs '%s/%s'.\n" "${worker}" "${the_worker_snapshot}" "${ezjail_jailzfs}" "${worker}"
      continue
    fi

    # We need to restart and rollback jail, iff
    # 1) worker dir does not exist (then we need to initially create one)
    # 2) worker dir mutex is older than timeout
    # 3) worker dir done token is set
    [ -e "${worker_dir}/taken" ] && birthtime=$( /usr/bin/stat -f %B "${worker_dir}/taken" ) || birthtime=${timeout}
    if [ ! -d "${worker_dir}" -o -e "${worker_dir}/done" -o "${birthtime}" -lt "${timeout}" ]; then

      # to avoid interferences with stale claim/release scripts remove them
      /bin/rm -rf "${worker_dir}/release" "${worker_dir}/claim" "${worker_dir}/ip"

      /usr/local/bin/ezjail-admin stop "${worker}"

      # if we can't rollback, do not re-cycle the jail
      /sbin/zfs rollback -R ${worker_snap} || continue

      cleanup=YES
    fi

    # If jail's not running (anymore), restart
    is_ezjail_alive "${worker}" || /usr/local/bin/ezjail-admin start "${worker}" || continue

    # Re-cyle the worker by cleaning it's work dir
    /bin/mkdir -p "${worker_dir}" || continue

    # Copy claim and release scripts into worker dir
    printf "#!/bin/sh\n\n/usr/bin/touch %s/done\n/usr/bin/pkill -HUP -f %s\n" ${worker_suffix} ${the_proctitle} > "${worker_dir}/release"
    printf "#!/bin/sh\n\n/usr/bin/mktemp %s 2> /dev/null >/dev/null\nexit \$?\n" "${worker_suffix}/taken" > "${worker_dir}/claim"
    /bin/chmod 0755 "${worker_dir}/claim" "${worker_dir}/release"

    # Dump the jail's IP address so the master jail knows whom to talk to
    : ${worker_ipport="$( /usr/sbin/jls -j ${worker} -n ip4.addr ):"}
    printf "%s\n" "${worker_ipport##*=}" > "${worker_dir}/ip"

    # Finally remove all tokens, jail is available, again
    [ "${cleanup}" ] && /bin/rm -rf "${worker_dir}"/done "${worker_dir}"/taken
  done

  # Finally insert probe into master jail to allow triggering the reaper
  which jaildaemon > /dev/null 2> /dev/null || exerr "Warning: jaildaemon is not installed. Working with cron cleanup only."
  is_ezjail_alive "${the_master_jail}" || exerr "Warning: master jail is not running. No jaildaemon probe launched."

  jail_name=$( printf ${the_master_jail} | /usr/bin/tr -c '[:alnum:]' _ )
  /usr/bin/pgrep -f ${the_proctitle} > /dev/null 2>/dev/null
  [ $? -eq 1 ] && /usr/local/bin/jaildaemon -c "${the_dispatch_script}" -j ${jail_name} -r -t ${the_proctitle}

  /bin/rm -r "${the_dispatch_lock}"
}

does_snapshot_exist() {
  /sbin/zfs list -t snapshot $1 >/dev/null 2>/dev/null
  return $?
}

does_ezjail_exist() {
  /usr/local/bin/ezjail-admin config -r test "$1" >/dev/null 2> /dev/null
  return $?
}

is_ezjail_alive() {
  jail_name=$( printf $1 | /usr/bin/tr -c '[:alnum:]' _ )
  /usr/sbin/jls -n -j "${jail_name}" > /dev/null 2> /dev/null
  return $?
}

# After function definitions, main() can use them
main "$@"

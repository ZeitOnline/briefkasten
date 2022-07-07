#!/bin/bash
#
# note that for this to work the `briefkasten` checkout needs to be located
# "inside" the `briefkasten-config` checkout using the submodule setup as
# added in https://github.com/ZeitOnline/briefkasten-config/commit/05e9da7c

docker build -t briefkasten-ploy .
docker run -it \
	-v $PWD:/briefkasten \
	-v $PWD/../../etc:/briefkasten/etc \
	--volume /run/host-services/ssh-auth.sock:/run/host-services/ssh-auth.sock:ro \
	--env SSH_AUTH_SOCK="/run/host-services/ssh-auth.sock" \
	briefkasten-ploy

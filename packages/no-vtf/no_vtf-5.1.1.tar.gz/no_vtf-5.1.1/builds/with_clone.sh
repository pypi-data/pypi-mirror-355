#!/bin/bash

# SPDX-FileCopyrightText: b5327157 <b5327157@protonmail.com>
#
# SPDX-License-Identifier: GPL-3.0-or-later

set -e
source builds/common.shlib
set -x

git_cmd=()
while [ "$1" != '--' ]; do
	[ -n "$1" ]
	git_cmd+=("$1")
	shift
done
shift

[ -n "$1" ]

tmpdir="$(mktemp --directory)"
cd "$tmpdir"

# realpath hack to workaround Wine not accepting absolute Unix paths as-is
relpath="$(realpath --relative-to=. -- "$OLDPWD")"
command -- "${git_cmd[@]}" -c init.defaultBranch=master clone --quiet --no-checkout -- "$relpath" .

command -- "${git_cmd[@]}" checkout --quiet HEAD

exec -- "$@"

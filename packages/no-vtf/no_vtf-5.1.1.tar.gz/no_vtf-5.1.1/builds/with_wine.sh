#!/bin/bash

# SPDX-FileCopyrightText: b5327157 <b5327157@protonmail.com>
#
# SPDX-License-Identifier: GPL-3.0-or-later

set -e
source builds/common.shlib
set -x

[ -n "$1" ]
workdir="$1"
shift

[ -n "$1" ]

mkdir -p -- "$workdir"
pushd -- "$workdir" >/dev/null

WINEPREFIX="$(readlink --canonicalize prefix)"
export WINEPREFIX
export WINEDEBUG='-all,err+mscoree'
export WINEDLLOVERRIDES='winemenubuilder.exe=d'

alias nuget-install='nuget install -DirectDownload -Verbosity quiet -NonInteractive'

if [ ! -e "$WINEPREFIX"'/.update-timestamp' ]; then
	wineboot --init

	curl --location --output nuget.exe 'https://aka.ms/nugetclidl'

	wine nuget-install python -Version 3.10.11
	pushd python.*/tools >/dev/null
	ln -s python.exe python3.10.exe
	popd >/dev/null

	wine nuget-install GitForWindows
fi

winepaths=()
winepaths+=("$(winepath --windows python.*/tools)")
winepaths+=("$(winepath --windows GitForWindows.*/tools/cmd)")
printf -v WINEPATH '%s;' "${winepaths[@]}"
export WINEPATH

popd >/dev/null

command -- "$@"

wineserver --wait

#!/bin/bash

# SPDX-FileCopyrightText: b5327157 <b5327157@protonmail.com>
#
# SPDX-License-Identifier: GPL-3.0-or-later

set -e
source builds/common.shlib
set -x

ARCHIVE='release.tar.gz'
SITE='b5327157.srht.site'
SUBDIRECTORY='no_vtf/release'

acurl()
(
	set +x
	curl --oauth2-bearer "${OAUTH2_TOKEN:?}" "$@" || {
		exit_code="$?"
		set -x
		return "$exit_code"
	}
	set -x
)

directory="$1"
shift

tar cvzf "$ARCHIVE" --transform 's,^,'"$SUBDIRECTORY"'/,' --show-transformed-names -C "$directory" -- "$@"
acurl --form content=@"$ARCHIVE" 'https://pages.sr.ht/publish/'"$SITE"

for file_path in "$@"; do
	diff --report-identical-files -- "$directory"/"$file_path" <(curl 'https://'"$SITE"/"$SUBDIRECTORY"/"$file_path" || true)
done

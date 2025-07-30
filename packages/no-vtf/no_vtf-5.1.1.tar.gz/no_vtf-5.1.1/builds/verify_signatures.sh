#!/bin/bash

# SPDX-FileCopyrightText: b5327157 <b5327157@protonmail.com>
#
# SPDX-License-Identifier: GPL-3.0-or-later

set -e
source builds/common.shlib
set -x

gpg --recv-keys 46C4ACD8B7B3F77DC8C2E8ED1C3724DFF9CEAF64 # b5327157@protonmail.com

nproc="$(nproc)"
git rev-list --exclude=refs/stash --all | xargs -I '{}' --no-run-if-empty --max-args 1 --max-procs "$nproc" -- chronic -- sh -c 'rev="$1"; git verify-commit "$rev" || { echo "Cannot verify GPG signature of commit ${rev}"; exit 255; }' sh '{}'
git tag --list | xargs -I '{}' --no-run-if-empty --max-args 1 --max-procs "$nproc" -- chronic -- sh -c 'rev="$1"; git verify-tag "$rev" || { echo "Cannot verify GPG signature of tag ${rev}"; exit 255; }' sh '{}'

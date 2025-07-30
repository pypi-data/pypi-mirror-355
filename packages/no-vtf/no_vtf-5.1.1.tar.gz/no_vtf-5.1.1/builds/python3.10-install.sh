#!/bin/bash

# SPDX-FileCopyrightText: b5327157 <b5327157@protonmail.com>
#
# SPDX-License-Identifier: GPL-3.0-or-later

set -e
source builds/common.shlib
set -x

sudo apt-get install build-essential
sudo apt-get install libffi-dev libssl-dev zlib1g-dev liblzma-dev libsqlite3-dev

PREFIX='/usr/local'

tmpdir="$(mktemp --directory)"
cd "$tmpdir"

git -c init.defaultBranch=master clone --quiet --branch 3.10 --depth 1 'https://github.com/python/cpython.git' .

export LD_RUN_PATH="$PREFIX"'/lib'

chronic ./configure --prefix "$PREFIX" --enable-shared --with-lto

nproc="$(nproc)"
make --silent --jobs "$nproc"

sudo make altinstall >/dev/null

python3.10 --version

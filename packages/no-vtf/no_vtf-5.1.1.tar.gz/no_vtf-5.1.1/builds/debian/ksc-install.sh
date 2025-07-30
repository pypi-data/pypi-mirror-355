#!/bin/bash

# SPDX-FileCopyrightText: b5327157 <b5327157@protonmail.com>
#
# SPDX-License-Identifier: GPL-3.0-or-later

set -e
source builds/common.shlib
set -x

tmpdir="$(mktemp --directory)"
cd "$tmpdir"

curl --location --remote-name 'https://github.com/kaitai-io/kaitai_struct_compiler/releases/download/0.10/kaitai-struct-compiler_0.10_all.deb'
sudo apt-get install './kaitai-struct-compiler_0.10_all.deb'

#!/bin/bash

# SPDX-FileCopyrightText: b5327157 <b5327157@protonmail.com>
#
# SPDX-License-Identifier: GPL-3.0-or-later

set -e
source builds/common.shlib
set -x

chsh --shell /bin/bash

echo 'debconf debconf/frontend select Noninteractive' | sudo debconf-set-selections

# prevent alias expansion of apt-get as this is installing its prerequisites
command sudo apt-get --quiet --quiet --yes update
command sudo apt-get --quiet --quiet --yes install moreutils >/dev/null

sudo apt-get install bat

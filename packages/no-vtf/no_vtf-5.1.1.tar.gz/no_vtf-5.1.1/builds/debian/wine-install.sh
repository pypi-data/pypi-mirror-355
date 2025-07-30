#!/bin/bash

# SPDX-FileCopyrightText: b5327157 <b5327157@protonmail.com>
#
# SPDX-License-Identifier: GPL-3.0-or-later

set -e
source builds/common.shlib
set -x

WINEHQ_KEYRING_PATH='/usr/share/keyrings/winehq-archive-keyring.gpg'

sudo dpkg --add-architecture i386

curl 'https://dl.winehq.org/wine-builds/winehq.key' |
	gpg --dearmor |
	sudo tee -- "$WINEHQ_KEYRING_PATH" >/dev/null

echo 'deb' \
	'[signed-by='"$WINEHQ_KEYRING_PATH"']' \
	'https://dl.winehq.org/wine-builds/ubuntu focal main' |
	sudo tee --append /etc/apt/sources.list >/dev/null

sudo apt-get update

sudo apt-get install --install-recommends winehq-devel

MONO_BINARY_TARBALL_URL='https://dl.winehq.org/wine/wine-mono/10.0.0/wine-mono-10.0.0-x86.tar.xz'
MONO_DEST_DIR='/opt/wine-devel/share/wine/mono'
sudo mkdir -p -- "$MONO_DEST_DIR"
curl -- "$MONO_BINARY_TARBALL_URL" |
	sudo tar xJ -C "$MONO_DEST_DIR"

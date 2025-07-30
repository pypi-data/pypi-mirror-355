#!/bin/bash

# SPDX-FileCopyrightText: b5327157 <b5327157@protonmail.com>
#
# SPDX-License-Identifier: GPL-3.0-or-later

set -e
source builds/common.shlib

commands=(
	'stty -onlcr'
	'export TERM="xterm-256color"'
	'export COLORTERM="truecolor"'
	'exec -- '"${*@Q}"
)
command_string=$(
	IFS=';'
	printf '%s' "${commands[*]}"
)

builds/with_pty.sh \
	bash -c "$command_string" |
	stdbuf -oL sed -E 's/\x1b(\[(\?25[hl]|0*K)|\]([0-9]*;[[:print:]]*(\x07|\x1b\\)))//g' |
	stdbuf -oL sed -E 's/\x1b\[1?C/ /g' |
	(
		set +x

		while IFS=$'\r' read -r -a cr_parts; do
			last_part=''
			for part in "${cr_parts[@]}"; do
				if [ -n "$part" ]; then
					last_part="$part"
				fi
			done

			printf '%s\n' "$last_part"
		done
	)

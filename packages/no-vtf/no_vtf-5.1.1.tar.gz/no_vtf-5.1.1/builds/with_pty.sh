#!/bin/bash

# SPDX-FileCopyrightText: b5327157 <b5327157@protonmail.com>
#
# SPDX-License-Identifier: GPL-3.0-or-later

set -e
source builds/common.shlib

commands=(
	'[ "$(stty size | awk "{ print \$1 * \$2 }")" != 0 ] || stty cols 32767 rows 32767'
	'exec -- '"${*@Q}"
)
command_string=$(
	IFS=';'
	printf '%s' "${commands[*]}"
)

SHELL=/bin/bash exec script --quiet --return --command "$command_string" /dev/null

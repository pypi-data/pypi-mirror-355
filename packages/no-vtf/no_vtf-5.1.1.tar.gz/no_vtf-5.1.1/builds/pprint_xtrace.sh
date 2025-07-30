#!/bin/bash

# SPDX-FileCopyrightText: b5327157 <b5327157@protonmail.com>
#
# SPDX-License-Identifier: GPL-3.0-or-later

set -e
source builds/common.shlib

DICES=(⬚ ⚀ ⚁ ⚂ ⚃ ⚄ ⚅)

highlighter()
{
	if [ ! -v BAT ]; then
		for BAT in batcat bat ''; do
			if command -v -- "$BAT" >/dev/null; then
				break
			fi
		done
	fi

	if [ -n "$BAT" ]; then
		command -- "$BAT" --style=plain --paging=never --wrap never --color always --theme 1337 --language bash
	else
		cat
	fi
}

replicate_str()
{
	if [ "$1" -ge 1 ] 2>/dev/null; then
		set -o noglob
		# shellcheck disable=SC2207
		local seq=($(seq 1 "$1"))
		set +o noglob

		printf '%.0s'"$2" "${seq[@]}"
	else
		[ "$1" -eq 0 ]
	fi
}

PS4='+<${SHLVL}> ' \
	command -- "$@" |&
	(
		set +x

		nesting_indent=''
		while IFS='' read -r line; do
			if [[ $line =~ ^([^\+]*)(\++)\<([[:digit:]]+)\>[[:blank:]](.+)$ ]]; then
				leftovers="${BASH_REMATCH[1]}"
				indirection_level="${#BASH_REMATCH[2]}"
				nesting_level="${BASH_REMATCH[3]}"

				if ! [ "$SHLVL" -eq "$SHLVL" ] || ! [ "$nesting_level" -eq "$nesting_level" ]; then
					printf '%s%s\n' "$nesting_indent" "$line"
					continue
				fi

				if [ -n "$leftovers" ]; then
					printf '%s%s\n' "$nesting_indent" "$leftovers"
				fi

				relative_nesting_level=$((nesting_level - SHLVL))

				nesting_indent="$(replicate_str $((relative_nesting_level - 1)) '  ')"
				nesting_symbol="${DICES[${relative_nesting_level}]:-${DICES[0]}}"
				indirection_indent="$(replicate_str $((indirection_level - 1)) '  ')"
				highlighted="$(highlighter <<<"${BASH_REMATCH[4]}")"

				printf '%s%s %s%s\n' "$nesting_indent" "$nesting_symbol" "$indirection_indent" "$highlighted"
			else
				printf '%s%s\n' "$nesting_indent" "$line"
			fi
		done
	)

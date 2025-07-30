#!/usr/bin/env python3

# SPDX-FileCopyrightText: b5327157 <b5327157@protonmail.com>
#
# SPDX-License-Identifier: GPL-3.0-or-later

import subprocess
import sys

from typing import NoReturn


def main() -> NoReturn:
    subprocess.run(
        [
            sys.executable,
            "-m",
            "pip",
            "--quiet",
            "--no-input",
            "--disable-pip-version-check",
            "install",
            "--no-warn-script-location",
            "nox[uv]",
        ],
        check=True,
    )

    sys.exit(
        subprocess.run(
            [
                sys.executable,
                "-m",
                "nox",
                "--non-interactive",
                *sys.argv[1:],
            ]
        ).returncode
    )


if __name__ == "__main__":
    main()

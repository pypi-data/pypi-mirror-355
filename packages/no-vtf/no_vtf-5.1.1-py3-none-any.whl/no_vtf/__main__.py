# SPDX-FileCopyrightText: b5327157 <b5327157@protonmail.com>
#
# SPDX-License-Identifier: LGPL-3.0-or-later

from no_vtf.main import COMPLETE_VAR, main_command
from no_vtf.task_runner import TaskRunner


def _main() -> None:
    TaskRunner.initialize()

    main_command(complete_var=COMPLETE_VAR)


if __name__ == "__main__":
    _main()

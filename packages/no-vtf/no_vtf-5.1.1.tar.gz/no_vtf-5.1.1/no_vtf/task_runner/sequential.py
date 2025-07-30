# SPDX-FileCopyrightText: b5327157 <b5327157@protonmail.com>
#
# SPDX-License-Identifier: LGPL-3.0-or-later

from collections.abc import Iterator, Sequence
from typing import TypeVar, Union

from no_vtf.typing import mypyc_attr

from .task_runner import Task, TaskRunner

_A_co = TypeVar("_A_co", covariant=True)


@mypyc_attr(allow_interpreted_subclasses=True)
class SequentialRunner(TaskRunner):
    def __call__(
        self, tasks: Sequence[Task[_A_co]]
    ) -> Iterator[tuple[Task[_A_co], Union[_A_co, Exception]]]:
        for task in tasks:
            yield self.process(task)

    @staticmethod
    def process(
        task: Task[_A_co],
    ) -> tuple[Task[_A_co], Union[_A_co, Exception]]:
        try:
            result = task()
            return (task, result)
        except Exception as exception:
            return (task, exception)

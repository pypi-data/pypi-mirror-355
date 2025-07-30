# SPDX-FileCopyrightText: b5327157 <b5327157@protonmail.com>
#
# SPDX-License-Identifier: LGPL-3.0-or-later

from __future__ import annotations

from abc import abstractmethod
from collections.abc import Iterator, Sequence
from typing import Protocol, TypeVar, Union

# define all task runners for TaskRunner.initialize()
import no_vtf.task_runner  # noqa: F401  # pyright: ignore [reportUnusedImport]

from no_vtf.typing import mypyc_attr

_A_co = TypeVar("_A_co", covariant=True)


class Task(Protocol[_A_co]):
    def __call__(self) -> _A_co: ...


@mypyc_attr(allow_interpreted_subclasses=True)
class TaskRunner:
    @classmethod
    def initialize(cls, *, _recursive: bool = True) -> None:
        if _recursive:
            for subclass in cls.__subclasses__():
                subclass.initialize()

    @abstractmethod
    def __call__(
        self, tasks: Sequence[Task[_A_co]]
    ) -> Iterator[tuple[Task[_A_co], Union[_A_co, Exception]]]: ...

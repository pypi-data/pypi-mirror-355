# SPDX-FileCopyrightText: b5327157 <b5327157@protonmail.com>
#
# SPDX-License-Identifier: LGPL-3.0-or-later

from __future__ import annotations

from collections.abc import Callable
from typing import Final, Generic, Optional, TypeVar, cast

from no_vtf.typing import mypyc_attr

_A = TypeVar("_A")
_A_co = TypeVar("_A_co", covariant=True)
_B_co = TypeVar("_B_co", covariant=True)


@mypyc_attr(allow_interpreted_subclasses=True)
class Deferred(Generic[_A_co]):
    @classmethod
    def pure(cls, a: _A, /) -> Deferred[_A]:
        return Deferred(lambda: a)

    @classmethod
    def join(cls, a: Deferred[Deferred[_A_co]], /) -> Deferred[_A_co]:
        return Deferred(lambda: a()())

    def __init__(self, thunk: Callable[[], _A_co], /) -> None:
        self._thunk: Final = thunk
        self._result: Optional[_A_co] = None
        self._result_valid = False

    def __call__(self) -> _A_co:
        if not self._result_valid:
            self._result = self._thunk()
            self._result_valid = True

        return cast(_A_co, self._result)

    def map(self, f: Callable[[_A_co], _B_co], /) -> Deferred[_B_co]:
        return Deferred(lambda: f(self()))

    def apply(self, f: Deferred[Callable[[_A_co], _B_co]], /) -> Deferred[_B_co]:
        return Deferred(lambda: f()(self()))

    def bind(self, f: Callable[[_A_co], Deferred[_B_co]], /) -> Deferred[_B_co]:
        return Deferred(lambda: f(self())())

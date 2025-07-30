# SPDX-FileCopyrightText: b5327157 <b5327157@protonmail.com>
#
# SPDX-License-Identifier: LGPL-3.0-or-later

from __future__ import annotations

from abc import abstractmethod
from typing import Any, Final, Generic, Literal, Optional, TypeVar, cast, overload

from typing_extensions import Self

# define every IO for IO.initialize()
import no_vtf.core.image.io  # noqa: F401  # pyright: ignore [reportUnusedImport]

from no_vtf.typing import mypyc_attr

_O = TypeVar("_O")
_T = TypeVar("_T")


@mypyc_attr(allow_interpreted_subclasses=True)
class _Options(Generic[_O]):
    def __init__(self, copy: Optional[_O] = None, /) -> None:
        if copy:
            self.merge(copy, non_none=False)

    def clone(self) -> Self:
        return type(self)(cast(_O, self))

    @abstractmethod
    def merge(self, other: _O, /, *, non_none: bool = True) -> Self:
        return self

    @overload
    @classmethod
    def rightmost(cls, first: _T, /, *, non_none: bool = True) -> _T: ...

    @overload
    @classmethod
    def rightmost(cls, first: _T, /, *rest: Optional[_T], non_none: Literal[True]) -> _T: ...

    @overload
    @classmethod
    def rightmost(
        cls, first: _T, /, *rest: Optional[_T], non_none: bool = True
    ) -> Optional[_T]: ...

    @classmethod
    def rightmost(cls, first: _T, /, *rest: Optional[_T], non_none: bool = True) -> Optional[_T]:
        old: Optional[_T] = first
        for new in rest:
            if new is not None or not non_none:
                old = new

        return old


@mypyc_attr(allow_interpreted_subclasses=True)
class IOWriteOptions(_Options["IOWriteOptions"]):
    def merge(self, other: IOWriteOptions, /, *, non_none: bool = True) -> Self:
        return super().merge(other, non_none=non_none)


@mypyc_attr(allow_interpreted_subclasses=True)
class IOReadbackOptions(_Options["IOReadbackOptions"]):
    def merge(self, other: IOReadbackOptions, /, *, non_none: bool = True) -> Self:
        return super().merge(other, non_none=non_none)


@mypyc_attr(allow_interpreted_subclasses=True)
class IO:
    @classmethod
    def initialize(cls, *, _recursive: bool = True) -> None:
        if _recursive:
            for subclass in cls.__subclasses__():
                subclass.initialize()

    def __init__(
        self,
        *,
        write_defaults: IOWriteOptions = IOWriteOptions(),
        readback_defaults: IOReadbackOptions = IOReadbackOptions(),
        **kwargs: Any,
    ) -> None:
        if kwargs:
            raise TypeError(f"got unexpected keyword arguments: {[*kwargs.keys()]}")

        self._write_defaults: Final = write_defaults.clone()
        self._readback_defaults: Final = readback_defaults.clone()

    @property
    def write_defaults(self) -> IOWriteOptions:
        return self._write_defaults.clone()

    @property
    def readback_defaults(self) -> IOReadbackOptions:
        return self._readback_defaults.clone()

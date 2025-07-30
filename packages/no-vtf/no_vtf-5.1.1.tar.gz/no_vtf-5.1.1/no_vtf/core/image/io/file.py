# SPDX-FileCopyrightText: b5327157 <b5327157@protonmail.com>
#
# SPDX-License-Identifier: LGPL-3.0-or-later

from __future__ import annotations

import pathlib

from abc import abstractmethod
from typing import Generic, Optional, TypeVar

from typing_extensions import Self

from no_vtf.core.image import AnyImage
from no_vtf.typing import mypyc_attr

from .io import IO, IOReadbackOptions, IOWriteOptions

_T_contra = TypeVar("_T_contra", bound=pathlib.Path, contravariant=True)
_I_contra = TypeVar("_I_contra", bound=AnyImage, contravariant=True)


@mypyc_attr(allow_interpreted_subclasses=True)
class FileIOWriteOptions(IOWriteOptions):
    def __init__(self, copy: Optional[IOWriteOptions] = None, /) -> None:
        self.overwrite: Optional[bool] = None
        self.mkdir_parents: Optional[bool] = None

        super().__init__(copy)

    def merge(self, other: IOWriteOptions, /, *, non_none: bool = True) -> Self:
        if isinstance(other, FileIOWriteOptions):
            self.overwrite = self.rightmost(self.overwrite, other.overwrite, non_none=non_none)
            self.mkdir_parents = self.rightmost(
                self.mkdir_parents, other.mkdir_parents, non_none=non_none
            )

        return super().merge(other, non_none=non_none)


@mypyc_attr(allow_interpreted_subclasses=True)
class FileIOReadbackOptions(IOReadbackOptions):
    pass


@mypyc_attr(allow_interpreted_subclasses=True)
class FileIO(IO, Generic[_T_contra, _I_contra]):
    @abstractmethod
    def write_file(
        self,
        path: _T_contra,
        /,
        *images: _I_contra,
        options: IOWriteOptions = IOWriteOptions(),
    ) -> bool:
        merged_options = FileIOWriteOptions(self.write_defaults).merge(options)
        overwrite = merged_options.rightmost(True, merged_options.overwrite)
        mkdir_parents = merged_options.rightmost(False, merged_options.mkdir_parents)

        if not overwrite and path.is_file():
            return False

        if mkdir_parents:
            path.parent.mkdir(parents=True, exist_ok=True)

        return True

    @abstractmethod
    def readback_file(
        self,
        path: _T_contra,
        /,
        *images: _I_contra,
        options: IOReadbackOptions = IOReadbackOptions(),
    ) -> bool:
        return True

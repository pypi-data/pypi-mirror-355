# SPDX-FileCopyrightText: b5327157 <b5327157@protonmail.com>
#
# SPDX-License-Identifier: LGPL-3.0-or-later

import pathlib

from typing import TypeAlias, TypeVar

from no_vtf.core.image import AnyImageWithRawData
from no_vtf.typing import mypyc_attr

from .file import FileIO, FileIOReadbackOptions, FileIOWriteOptions
from .io import IOReadbackOptions, IOWriteOptions


@mypyc_attr(allow_interpreted_subclasses=True)
class RawIOWriteOptions(FileIOWriteOptions):
    pass


@mypyc_attr(allow_interpreted_subclasses=True)
class RawIOReadbackOptions(FileIOReadbackOptions):
    pass


_T_contra = TypeVar("_T_contra", bound=pathlib.Path, contravariant=True)
_I_contra = TypeVar("_I_contra", bound=AnyImageWithRawData, contravariant=True)


@mypyc_attr(allow_interpreted_subclasses=True)
class RawIO(FileIO[_T_contra, _I_contra]):
    def write_file(
        self,
        path: _T_contra,
        /,
        *images: _I_contra,
        options: IOWriteOptions = IOWriteOptions(),
    ) -> bool:
        if not super().write_file(path, *images, options=options):
            return False

        with path.open("wb") as file:
            for image in images:
                data = image.raw
                file.write(data)

        return True

    def readback_file(
        self,
        path: _T_contra,
        /,
        *images: _I_contra,
        options: IOReadbackOptions = IOReadbackOptions(),
    ) -> bool:
        if not super().readback_file(path, *images, options=options):
            return False

        with path.open("rb") as file:
            for image in images:
                data = image.raw

                read_data = file.read(len(data))
                if data != read_data:
                    raise ValueError(f"{path!r}: Data differs from what is in the file")

            if file.read():
                raise ValueError(f"{path!r}: Data differs from what is in the file")

        return True


AnyRawIO: TypeAlias = RawIO[pathlib.Path, AnyImageWithRawData]

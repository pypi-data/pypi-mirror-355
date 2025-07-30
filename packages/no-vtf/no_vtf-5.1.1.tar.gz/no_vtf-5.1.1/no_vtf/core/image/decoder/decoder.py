# SPDX-FileCopyrightText: b5327157 <b5327157@protonmail.com>
#
# SPDX-License-Identifier: LGPL-3.0-or-later

from typing import Protocol, TypeVar

from no_vtf.core.image import AnyImageWithRawData

_I_co = TypeVar("_I_co", bound=AnyImageWithRawData, covariant=True)


class ImageDecoder(Protocol[_I_co]):
    def __call__(
        self, encoded_image: bytes, logical_width: int, logical_height: int, /
    ) -> _I_co: ...

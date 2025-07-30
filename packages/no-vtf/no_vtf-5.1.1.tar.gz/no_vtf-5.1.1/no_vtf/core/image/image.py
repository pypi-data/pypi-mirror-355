# SPDX-FileCopyrightText: b5327157 <b5327157@protonmail.com>
#
# SPDX-License-Identifier: LGPL-3.0-or-later

from __future__ import annotations

import typing

from typing import Final, Generic, Literal, TypeAlias, TypeGuard, TypeVar, Union

import numpy as np
import numpy.typing as npt

from no_vtf.functional import Deferred
from no_vtf.typing import mypyc_attr

ImageDataTypesLDR: TypeAlias = np.uint8 | np.uint16
ImageDataTypesHDR: TypeAlias = np.float16 | np.float32

ImageDataTypes: TypeAlias = Union[ImageDataTypesLDR, ImageDataTypesHDR]

ImageChannels = Literal["rgb", "rgba", "l", "la", "a"]
ImageDynamicRange = Literal["ldr", "hdr"]

_Id_co = TypeVar("_Id_co", bound=ImageDataTypes, covariant=True)
_Ic_co = TypeVar("_Ic_co", bound=ImageChannels, covariant=True)


@mypyc_attr(allow_interpreted_subclasses=True)
class Image(Generic[_Id_co, _Ic_co]):
    def __init__(
        self,
        *,
        data: Deferred[npt.NDArray[_Id_co]],
        dtype: np.dtype[_Id_co],
        channels: _Ic_co,
    ) -> None:
        self.data: Final = data
        self.dtype: Final = dtype
        self.channels: Final = channels

    @property
    def dynamic_range(self) -> ImageDynamicRange:
        ldr = _is_ldr(self.dtype)
        hdr = _is_hdr(self.dtype)
        assert ldr != hdr  # noqa S101 debug check

        return "hdr" if hdr else "ldr"

    @staticmethod
    def is_ldr(image: Image[ImageDataTypes, _Ic_co]) -> TypeGuard[Image[ImageDataTypesLDR, _Ic_co]]:
        return image.dynamic_range == "ldr"

    @staticmethod
    def is_hdr(image: Image[ImageDataTypes, _Ic_co]) -> TypeGuard[Image[ImageDataTypesHDR, _Ic_co]]:
        return image.dynamic_range == "hdr"


AnyImage: TypeAlias = Image[ImageDataTypes, ImageChannels]


@mypyc_attr(allow_interpreted_subclasses=True)
class ImageWithRawData(Image[_Id_co, _Ic_co]):
    def __init__(
        self,
        *,
        raw: bytes,
        data: Deferred[npt.NDArray[_Id_co]],
        dtype: np.dtype[_Id_co],
        channels: _Ic_co,
    ) -> None:
        super().__init__(data=data, dtype=dtype, channels=channels)

        self.raw: Final = raw


AnyImageWithRawData: TypeAlias = ImageWithRawData[ImageDataTypes, ImageChannels]


def _is_ldr(dtype: npt.DTypeLike) -> bool:
    ldr_dtypes = typing.get_args(ImageDataTypesLDR)
    return any(np.issubdtype(dtype, ldr_dtype) for ldr_dtype in ldr_dtypes)


def _is_hdr(dtype: npt.DTypeLike) -> bool:
    hdr_dtypes = typing.get_args(ImageDataTypesHDR)
    return any(np.issubdtype(dtype, hdr_dtype) for hdr_dtype in hdr_dtypes)

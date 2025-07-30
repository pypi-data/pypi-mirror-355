# SPDX-FileCopyrightText: b5327157 <b5327157@protonmail.com>
#
# SPDX-License-Identifier: LGPL-3.0-or-later

import functools

from typing import Literal

import numpy as np
import numpy.typing as npt

from no_vtf.core.image import ImageWithRawData
from no_vtf.functional import Deferred

from .ndarray import s3tc_bytes_to_ndarray


def decode_dxt1_rgb(
    encoded_image: bytes, logical_width: int, logical_height: int
) -> ImageWithRawData[np.uint8, Literal["rgb"]]:
    def thunk() -> npt.NDArray[np.uint8]:
        rgba8888 = s3tc_bytes_to_ndarray(
            encoded_image,
            logical_width,
            logical_height,
            np.uint8,
            mode="RGBA",
            n=1,
            pixel_format="DXT1",
        )
        rgb888: npt.NDArray[np.uint8] = rgba8888[..., :3]
        return rgb888

    return ImageWithRawData(
        raw=encoded_image, data=Deferred(thunk), dtype=np.dtype(np.uint8), channels="rgb"
    )


def decode_dxt1_rgba(
    encoded_image: bytes, logical_width: int, logical_height: int
) -> ImageWithRawData[np.uint8, Literal["rgba"]]:
    thunk = functools.partial(
        s3tc_bytes_to_ndarray,
        encoded_image,
        logical_width,
        logical_height,
        np.uint8,
        mode="RGBA",
        n=1,
        pixel_format="DXT1",
    )
    return ImageWithRawData(
        raw=encoded_image, data=Deferred(thunk), dtype=np.dtype(np.uint8), channels="rgba"
    )


def decode_dxt3(
    encoded_image: bytes, logical_width: int, logical_height: int
) -> ImageWithRawData[np.uint8, Literal["rgba"]]:
    thunk = functools.partial(
        s3tc_bytes_to_ndarray,
        encoded_image,
        logical_width,
        logical_height,
        np.uint8,
        mode="RGBA",
        n=2,
        pixel_format="DXT3",
    )
    return ImageWithRawData(
        raw=encoded_image, data=Deferred(thunk), dtype=np.dtype(np.uint8), channels="rgba"
    )


def decode_dxt5(
    encoded_image: bytes, logical_width: int, logical_height: int
) -> ImageWithRawData[np.uint8, Literal["rgba"]]:
    thunk = functools.partial(
        s3tc_bytes_to_ndarray,
        encoded_image,
        logical_width,
        logical_height,
        np.uint8,
        mode="RGBA",
        n=3,
        pixel_format="DXT5",
    )
    return ImageWithRawData(
        raw=encoded_image, data=Deferred(thunk), dtype=np.dtype(np.uint8), channels="rgba"
    )


def decode_bc4(
    encoded_image: bytes, logical_width: int, logical_height: int
) -> ImageWithRawData[np.uint8, Literal["l"]]:
    thunk = functools.partial(
        s3tc_bytes_to_ndarray,
        encoded_image,
        logical_width,
        logical_height,
        np.uint8,
        mode="L",
        n=4,
        pixel_format="bc4",
    )
    return ImageWithRawData(
        raw=encoded_image, data=Deferred(thunk), dtype=np.dtype(np.uint8), channels="l"
    )


def decode_bc5(
    encoded_image: bytes, logical_width: int, logical_height: int
) -> ImageWithRawData[np.uint8, Literal["rgb"]]:
    thunk = functools.partial(
        s3tc_bytes_to_ndarray,
        encoded_image,
        logical_width,
        logical_height,
        np.uint8,
        mode="RGB",
        n=5,
        pixel_format="bc5",
    )
    return ImageWithRawData(
        raw=encoded_image, data=Deferred(thunk), dtype=np.dtype(np.uint8), channels="rgb"
    )


def decode_ati2n(
    encoded_image: bytes, logical_width: int, logical_height: int
) -> ImageWithRawData[np.uint8, Literal["rgb"]]:
    def thunk() -> npt.NDArray[np.uint8]:
        grx888 = s3tc_bytes_to_ndarray(
            encoded_image,
            logical_width,
            logical_height,
            np.uint8,
            mode="RGB",
            n=5,
            pixel_format="bc5",
        )
        rgx888 = grx888[..., (1, 0, 2)]
        return rgx888

    return ImageWithRawData(
        raw=encoded_image, data=Deferred(thunk), dtype=np.dtype(np.uint8), channels="rgb"
    )


def decode_bc7(
    encoded_image: bytes, logical_width: int, logical_height: int
) -> ImageWithRawData[np.uint8, Literal["rgba"]]:
    thunk = functools.partial(
        s3tc_bytes_to_ndarray,
        encoded_image,
        logical_width,
        logical_height,
        np.uint8,
        mode="RGBA",
        n=7,
        pixel_format="bc7",
    )
    return ImageWithRawData(
        raw=encoded_image, data=Deferred(thunk), dtype=np.dtype(np.uint8), channels="rgba"
    )

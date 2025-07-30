# SPDX-FileCopyrightText: b5327157 <b5327157@protonmail.com>
#
# SPDX-License-Identifier: LGPL-3.0-or-later

from typing import Literal, Optional

import numpy as np
import numpy.typing as npt

from typing_extensions import deprecated

from no_vtf.core.image import ImageWithRawData
from no_vtf.core.image.decoder.raw import (
    decode_bgr888,
    decode_bgra8888,
    decode_rgb888,
    decode_rgba16161616_le,
)
from no_vtf.functional import Deferred


def decode_rgb888_bluescreen(
    encoded_image: bytes, width: int, height: int
) -> ImageWithRawData[np.uint8, Literal["rgba"]]:
    return _decode_bluescreen(decode_rgb888(encoded_image, width, height))


def decode_bgr888_bluescreen(
    encoded_image: bytes, width: int, height: int
) -> ImageWithRawData[np.uint8, Literal["rgba"]]:
    return _decode_bluescreen(decode_bgr888(encoded_image, width, height))


def _decode_bluescreen(
    image: ImageWithRawData[np.uint8, Literal["rgb"]]
) -> ImageWithRawData[np.uint8, Literal["rgba"]]:
    data = image.data.map(_decode_bluescreen_data)
    return ImageWithRawData(raw=image.raw, data=data, dtype=np.dtype(np.uint8), channels="rgba")


def _decode_bluescreen_data(rgb888: npt.NDArray[np.uint8]) -> npt.NDArray[np.uint8]:
    is_opaque: npt.NDArray[np.bool_] = rgb888 != (0, 0, 255)

    is_opaque_any = is_opaque.any(axis=2)
    assert not isinstance(is_opaque_any, np.bool)  # noqa S101 type narrowing

    is_opaque_any = is_opaque_any[..., np.newaxis]

    rgb888 *= is_opaque_any
    a8: npt.NDArray[np.uint8] = np.multiply(is_opaque_any, 255, dtype=np.uint8)

    rgba8888: npt.NDArray[np.uint8] = np.dstack((rgb888, a8))
    return rgba8888


def decode_bgra8888_hdr(
    encoded_image: bytes, width: int, height: int, *, overbright_factor: Optional[float]
) -> ImageWithRawData[np.float32, Literal["rgb"]]:
    def thunk() -> npt.NDArray[np.float32]:
        nonlocal overbright_factor
        if overbright_factor is None:
            overbright_factor = 16

        rgba8888 = decode_bgra8888(encoded_image, width, height).data()

        rgba32323232f: npt.NDArray[np.float32] = rgba8888.astype(np.float32) / 255.0
        rgba32323232f[:, :, [0, 1, 2]] *= rgba32323232f[:, :, [3]] * overbright_factor

        rgb323232f: npt.NDArray[np.float32] = rgba32323232f[..., :3]
        return rgb323232f

    return ImageWithRawData(
        raw=encoded_image, data=Deferred(thunk), dtype=np.dtype(np.float32), channels="rgb"
    )


def decode_rgba16161616_le_hdr(
    encoded_image: bytes, width: int, height: int
) -> ImageWithRawData[np.float32, Literal["rgba"]]:
    def thunk() -> npt.NDArray[np.float32]:
        rgba16161616 = decode_rgba16161616_le(encoded_image, width, height).data()
        # convert 4.12 fixed point stored as integer into floating point
        rgba32323232f: npt.NDArray[np.float32] = rgba16161616.astype(np.float32) / np.float32(
            1 << 12
        )
        return rgba32323232f

    return ImageWithRawData(
        raw=encoded_image, data=Deferred(thunk), dtype=np.dtype(np.float32), channels="rgba"
    )


@deprecated("Use decode_rgb888_bluescreen instead")
def decode_rgb_uint8_bluescreen(
    encoded_image: bytes, width: int, height: int
) -> ImageWithRawData[np.uint8, Literal["rgba"]]:
    return decode_rgb888_bluescreen(encoded_image, width, height)


@deprecated("Use decode_bgr888_bluescreen instead")
def decode_bgr_uint8_bluescreen(
    encoded_image: bytes, width: int, height: int
) -> ImageWithRawData[np.uint8, Literal["rgba"]]:
    return decode_bgr888_bluescreen(encoded_image, width, height)


@deprecated("Use decode_bgra8888_hdr instead")
def decode_bgra_uint8_hdr(
    encoded_image: bytes, width: int, height: int, *, overbright_factor: Optional[float]
) -> ImageWithRawData[np.float32, Literal["rgb"]]:
    return decode_bgra8888_hdr(encoded_image, width, height, overbright_factor=overbright_factor)


@deprecated("Use decode_rgba16161616_le_hdr instead")
def decode_rgba_uint16_le_hdr(
    encoded_image: bytes, width: int, height: int
) -> ImageWithRawData[np.float32, Literal["rgba"]]:
    return decode_rgba16161616_le_hdr(encoded_image, width, height)

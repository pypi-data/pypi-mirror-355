# SPDX-FileCopyrightText: b5327157 <b5327157@protonmail.com>
#
# SPDX-License-Identifier: LGPL-3.0-or-later

from typing import Literal

import numpy as np
import numpy.typing as npt

from typing_extensions import deprecated

from no_vtf.core.image import ImageWithRawData
from no_vtf.functional import Deferred

from .ndarray import raw_bytes_to_ndarray


def decode_rgb888(
    encoded_image: bytes, width: int, height: int
) -> ImageWithRawData[np.uint8, Literal["rgb"]]:
    data = Deferred(lambda: raw_bytes_to_ndarray(encoded_image, width, height, (0, 1, 2), np.uint8))
    return ImageWithRawData(raw=encoded_image, data=data, dtype=np.dtype(np.uint8), channels="rgb")


def decode_rgba8888(
    encoded_image: bytes, width: int, height: int
) -> ImageWithRawData[np.uint8, Literal["rgba"]]:
    data = Deferred(
        lambda: raw_bytes_to_ndarray(encoded_image, width, height, (0, 1, 2, 3), np.uint8)
    )
    return ImageWithRawData(raw=encoded_image, data=data, dtype=np.dtype(np.uint8), channels="rgba")


def decode_argb8888(
    encoded_image: bytes, width: int, height: int
) -> ImageWithRawData[np.uint8, Literal["rgba"]]:
    data = Deferred(
        lambda: raw_bytes_to_ndarray(encoded_image, width, height, (1, 2, 3, 0), np.uint8)
    )
    return ImageWithRawData(raw=encoded_image, data=data, dtype=np.dtype(np.uint8), channels="rgba")


def decode_bgr888(
    encoded_image: bytes, width: int, height: int
) -> ImageWithRawData[np.uint8, Literal["rgb"]]:
    data = Deferred(lambda: raw_bytes_to_ndarray(encoded_image, width, height, (2, 1, 0), np.uint8))
    return ImageWithRawData(raw=encoded_image, data=data, dtype=np.dtype(np.uint8), channels="rgb")


def decode_bgra8888(
    encoded_image: bytes, width: int, height: int
) -> ImageWithRawData[np.uint8, Literal["rgba"]]:
    data = Deferred(
        lambda: raw_bytes_to_ndarray(encoded_image, width, height, (2, 1, 0, 3), np.uint8)
    )
    return ImageWithRawData(raw=encoded_image, data=data, dtype=np.dtype(np.uint8), channels="rgba")


def decode_bgrx8888(
    encoded_image: bytes, width: int, height: int
) -> ImageWithRawData[np.uint8, Literal["rgb"]]:
    data = Deferred(
        lambda: raw_bytes_to_ndarray(encoded_image, width, height, (2, 1, 0, 3), np.uint8)
    ).map(lambda data: data[..., :3])
    return ImageWithRawData(raw=encoded_image, data=data, dtype=np.dtype(np.uint8), channels="rgb")


def decode_abgr8888(
    encoded_image: bytes, width: int, height: int
) -> ImageWithRawData[np.uint8, Literal["rgba"]]:
    data = Deferred(
        lambda: raw_bytes_to_ndarray(encoded_image, width, height, (3, 2, 1, 0), np.uint8)
    )
    return ImageWithRawData(raw=encoded_image, data=data, dtype=np.dtype(np.uint8), channels="rgba")


def decode_rgba16161616_be(
    encoded_image: bytes, width: int, height: int
) -> ImageWithRawData[np.uint16, Literal["rgba"]]:
    data = Deferred(
        lambda: raw_bytes_to_ndarray(encoded_image, width, height, (0, 1, 2, 3), np.uint16, ">")
    )
    return ImageWithRawData(
        raw=encoded_image, data=data, dtype=np.dtype(np.uint16), channels="rgba"
    )


def decode_rgba16161616_le(
    encoded_image: bytes, width: int, height: int
) -> ImageWithRawData[np.uint16, Literal["rgba"]]:
    data = Deferred(
        lambda: raw_bytes_to_ndarray(encoded_image, width, height, (0, 1, 2, 3), np.uint16, "<")
    )
    return ImageWithRawData(
        raw=encoded_image, data=data, dtype=np.dtype(np.uint16), channels="rgba"
    )


def decode_rgba16161616f_be(
    encoded_image: bytes, width: int, height: int
) -> ImageWithRawData[np.float16, Literal["rgba"]]:
    data = Deferred(
        lambda: raw_bytes_to_ndarray(encoded_image, width, height, (0, 1, 2, 3), np.float16, ">")
    )
    return ImageWithRawData(
        raw=encoded_image, data=data, dtype=np.dtype(np.float16), channels="rgba"
    )


def decode_rgba16161616f_le(
    encoded_image: bytes, width: int, height: int
) -> ImageWithRawData[np.float16, Literal["rgba"]]:
    data = Deferred(
        lambda: raw_bytes_to_ndarray(encoded_image, width, height, (0, 1, 2, 3), np.float16, "<")
    )
    return ImageWithRawData(
        raw=encoded_image, data=data, dtype=np.dtype(np.float16), channels="rgba"
    )


def decode_l8(
    encoded_image: bytes, width: int, height: int
) -> ImageWithRawData[np.uint8, Literal["l"]]:
    data = Deferred(lambda: raw_bytes_to_ndarray(encoded_image, width, height, (0,), np.uint8))
    return ImageWithRawData(raw=encoded_image, data=data, dtype=np.dtype(np.uint8), channels="l")


def decode_a8(
    encoded_image: bytes, width: int, height: int
) -> ImageWithRawData[np.uint8, Literal["a"]]:
    data = Deferred(lambda: raw_bytes_to_ndarray(encoded_image, width, height, (0,), np.uint8))
    return ImageWithRawData(raw=encoded_image, data=data, dtype=np.dtype(np.uint8), channels="a")


def decode_la88(
    encoded_image: bytes, width: int, height: int
) -> ImageWithRawData[np.uint8, Literal["la"]]:
    la88 = Deferred(lambda: raw_bytes_to_ndarray(encoded_image, width, height, (0, 1), np.uint8))
    return ImageWithRawData(raw=encoded_image, data=la88, dtype=np.dtype(np.uint8), channels="la")


def decode_uv88(
    encoded_image: bytes, width: int, height: int
) -> ImageWithRawData[np.uint8, Literal["rgb"]]:
    def thunk() -> npt.NDArray[np.uint8]:
        rg88 = raw_bytes_to_ndarray(encoded_image, width, height, (0, 1), np.uint8)
        b8: npt.NDArray[np.uint8] = np.zeros(rg88.shape[:-1], dtype=np.uint8)
        rgb888: npt.NDArray[np.uint8] = np.dstack((rg88, b8))
        return rgb888

    return ImageWithRawData(
        raw=encoded_image, data=Deferred(thunk), dtype=np.dtype(np.uint8), channels="rgb"
    )


def decode_uvwq8888(
    encoded_image: bytes, width: int, height: int
) -> ImageWithRawData[np.uint8, Literal["rgba"]]:
    data = Deferred(
        lambda: raw_bytes_to_ndarray(encoded_image, width, height, (0, 1, 2, 3), np.uint8)
    )
    return ImageWithRawData(raw=encoded_image, data=data, dtype=np.dtype(np.uint8), channels="rgba")


def decode_uvlx8888(
    encoded_image: bytes, width: int, height: int
) -> ImageWithRawData[np.uint8, Literal["rgb"]]:
    data = Deferred(
        lambda: raw_bytes_to_ndarray(encoded_image, width, height, (0, 1, 2, 3), np.uint8)
    ).map(lambda data: data[..., :3])
    return ImageWithRawData(raw=encoded_image, data=data, dtype=np.dtype(np.uint8), channels="rgb")


def decode_bgra4444(
    encoded_image: bytes, width: int, height: int
) -> ImageWithRawData[np.uint8, Literal["rgba"]]:
    def thunk() -> npt.NDArray[np.uint8]:
        bgra4444 = raw_bytes_to_ndarray(encoded_image, width, height, (0, 1), np.uint8)

        b8 = np.bitwise_and(bgra4444[..., [0]], 0x0F)
        b8 = np.bitwise_or(b8, np.left_shift(b8, 4))

        g8 = np.bitwise_and(bgra4444[..., [0]], 0xF0)
        g8 = np.bitwise_or(g8, np.right_shift(g8, 4))

        r8 = np.bitwise_and(bgra4444[..., [1]], 0x0F)
        r8 = np.bitwise_or(r8, np.left_shift(r8, 4))

        a8 = np.bitwise_and(bgra4444[..., [1]], 0xF0)
        a8 = np.bitwise_or(a8, np.right_shift(a8, 4))

        rgba8888: npt.NDArray[np.uint8] = np.dstack((r8, g8, b8, a8))
        return rgba8888

    return ImageWithRawData(
        raw=encoded_image, data=Deferred(thunk), dtype=np.dtype(np.uint8), channels="rgba"
    )


def decode_rgb565(
    encoded_image: bytes, width: int, height: int
) -> ImageWithRawData[np.uint8, Literal["rgb"]]:
    def thunk() -> npt.NDArray[np.uint8]:
        rgb565 = raw_bytes_to_ndarray(encoded_image, width, height, (0, 1), np.uint8)
        rgb565_uint16 = rgb565.view(np.dtype(np.uint16).newbyteorder("<"))[..., 0]

        r5 = np.bitwise_and(np.right_shift(rgb565_uint16, 0x0), 0x1F).astype(np.uint8)
        g6 = np.bitwise_and(np.right_shift(rgb565_uint16, 0x5), 0x3F).astype(np.uint8)
        b5 = np.bitwise_and(np.right_shift(rgb565_uint16, 0xB), 0x1F).astype(np.uint8)

        r8 = np.round(r5.astype(np.float64) / 31 * 255).astype(np.uint8)
        g8 = np.round(g6.astype(np.float64) / 63 * 255).astype(np.uint8)
        b8 = np.round(b5.astype(np.float64) / 31 * 255).astype(np.uint8)

        rgb888 = np.dstack((r8, g8, b8))
        return rgb888

    return ImageWithRawData(
        raw=encoded_image, data=Deferred(thunk), dtype=np.dtype(np.uint8), channels="rgb"
    )


def decode_bgr565(
    encoded_image: bytes, width: int, height: int
) -> ImageWithRawData[np.uint8, Literal["rgb"]]:
    def thunk() -> npt.NDArray[np.uint8]:
        bgr888 = decode_rgb565(encoded_image, width, height).data()
        rgb888 = bgr888[..., (2, 1, 0)]
        return rgb888

    return ImageWithRawData(
        raw=encoded_image, data=Deferred(thunk), dtype=np.dtype(np.uint8), channels="rgb"
    )


def decode_bgra5551(
    encoded_image: bytes, width: int, height: int
) -> ImageWithRawData[np.uint8, Literal["rgba"]]:
    def thunk() -> npt.NDArray[np.uint8]:
        bgra5551 = raw_bytes_to_ndarray(encoded_image, width, height, (0, 1), np.uint8)
        bgra5551_uint16 = bgra5551.view(np.dtype(np.uint16).newbyteorder("<"))[..., 0]

        b5 = np.bitwise_and(np.right_shift(bgra5551_uint16, 0x0), 0x1F).astype(np.uint8)
        g5 = np.bitwise_and(np.right_shift(bgra5551_uint16, 0x5), 0x1F).astype(np.uint8)
        r5 = np.bitwise_and(np.right_shift(bgra5551_uint16, 0xA), 0x1F).astype(np.uint8)
        a1 = np.bitwise_and(np.right_shift(bgra5551_uint16, 0xF), 0x01).astype(bool)

        rgb555 = np.dstack((r5, g5, b5))
        rgb888 = np.round(rgb555.astype(np.float64) / 31 * 255).astype(np.uint8)

        a8 = np.multiply(a1, 255, dtype=np.uint8)

        rgba888 = np.dstack((rgb888, a8))
        return rgba888

    return ImageWithRawData(
        raw=encoded_image, data=Deferred(thunk), dtype=np.dtype(np.uint8), channels="rgba"
    )


def decode_bgrx5551(
    encoded_image: bytes, width: int, height: int
) -> ImageWithRawData[np.uint8, Literal["rgb"]]:
    data = Deferred(decode_bgra5551(encoded_image, width, height).data).map(
        lambda data: data[..., :3]
    )
    return ImageWithRawData(raw=encoded_image, data=data, dtype=np.dtype(np.uint8), channels="rgb")


@deprecated("Use decode_rgb888 instead")
def decode_rgb_uint8(
    encoded_image: bytes, width: int, height: int
) -> ImageWithRawData[np.uint8, Literal["rgb"]]:
    return decode_rgb888(encoded_image, width, height)


@deprecated("Use decode_rgba8888 instead")
def decode_rgba_uint8(
    encoded_image: bytes, width: int, height: int
) -> ImageWithRawData[np.uint8, Literal["rgba"]]:
    return decode_rgba8888(encoded_image, width, height)


@deprecated("Use decode_argb8888 instead")
def decode_argb_uint8(
    encoded_image: bytes, width: int, height: int
) -> ImageWithRawData[np.uint8, Literal["rgba"]]:
    return decode_argb8888(encoded_image, width, height)


@deprecated("Use decode_bgr888 instead")
def decode_bgr_uint8(
    encoded_image: bytes, width: int, height: int
) -> ImageWithRawData[np.uint8, Literal["rgb"]]:
    return decode_bgr888(encoded_image, width, height)


@deprecated("Use decode_bgra8888 instead")
def decode_bgra_uint8(
    encoded_image: bytes, width: int, height: int
) -> ImageWithRawData[np.uint8, Literal["rgba"]]:
    return decode_bgra8888(encoded_image, width, height)


@deprecated("Use decode_bgrx8888 instead")
def decode_bgrx_uint8(
    encoded_image: bytes, width: int, height: int
) -> ImageWithRawData[np.uint8, Literal["rgb"]]:
    return decode_bgrx8888(encoded_image, width, height)


@deprecated("Use decode_abgr8888 instead")
def decode_abgr_uint8(
    encoded_image: bytes, width: int, height: int
) -> ImageWithRawData[np.uint8, Literal["rgba"]]:
    return decode_abgr8888(encoded_image, width, height)


@deprecated("Use decode_rgba16161616_be instead")
def decode_rgba_uint16_be(
    encoded_image: bytes, width: int, height: int
) -> ImageWithRawData[np.uint16, Literal["rgba"]]:
    return decode_rgba16161616_be(encoded_image, width, height)


@deprecated("Use decode_rgba16161616_le instead")
def decode_rgba_uint16_le(
    encoded_image: bytes, width: int, height: int
) -> ImageWithRawData[np.uint16, Literal["rgba"]]:
    return decode_rgba16161616_le(encoded_image, width, height)


@deprecated("Use decode_rgba16161616f_be instead")
def decode_rgba_float16_be(
    encoded_image: bytes, width: int, height: int
) -> ImageWithRawData[np.float16, Literal["rgba"]]:
    return decode_rgba16161616f_be(encoded_image, width, height)


@deprecated("Use decode_rgba16161616f_le instead")
def decode_rgba_float16_le(
    encoded_image: bytes, width: int, height: int
) -> ImageWithRawData[np.float16, Literal["rgba"]]:
    return decode_rgba16161616f_le(encoded_image, width, height)


@deprecated("Use decode_l8 instead")
def decode_l_uint8(
    encoded_image: bytes, width: int, height: int
) -> ImageWithRawData[np.uint8, Literal["l"]]:
    return decode_l8(encoded_image, width, height)


@deprecated("Use decode_a8 instead")
def decode_a_uint8(
    encoded_image: bytes, width: int, height: int
) -> ImageWithRawData[np.uint8, Literal["a"]]:
    return decode_a8(encoded_image, width, height)


@deprecated("Use decode_la88 instead")
def decode_la_uint8(
    encoded_image: bytes, width: int, height: int
) -> ImageWithRawData[np.uint8, Literal["la"]]:
    return decode_la88(encoded_image, width, height)


@deprecated("Use decode_uv88 instead")
def decode_uv_uint8(
    encoded_image: bytes, width: int, height: int
) -> ImageWithRawData[np.uint8, Literal["rgb"]]:
    return decode_uv88(encoded_image, width, height)


@deprecated("Use decode_uvwq8888 instead")
def decode_uvwq_uint8(
    encoded_image: bytes, width: int, height: int
) -> ImageWithRawData[np.uint8, Literal["rgba"]]:
    return decode_uvwq8888(encoded_image, width, height)


@deprecated("Use decode_uvlx8888 instead")
def decode_uvlx_uint8(
    encoded_image: bytes, width: int, height: int
) -> ImageWithRawData[np.uint8, Literal["rgb"]]:
    return decode_uvlx8888(encoded_image, width, height)


@deprecated("Use decode_bgra4444 instead")
def decode_bgra_uint4_le(
    encoded_image: bytes, width: int, height: int
) -> ImageWithRawData[np.uint8, Literal["rgba"]]:
    return decode_bgra4444(encoded_image, width, height)

# SPDX-FileCopyrightText: b5327157 <b5327157@protonmail.com>
#
# SPDX-License-Identifier: LGPL-3.0-or-later

from collections.abc import Sequence
from typing import Literal, Optional, TypeVar

import numpy as np
import numpy.typing as npt
import PIL.Image

from typing_extensions import deprecated

ByteOrder = Literal["S", "<", ">", "=", "|", "L", "B", "N", "I"]

_S = TypeVar("_S", bound=np.generic)


def raw_bytes_to_ndarray(
    image: bytes,
    width: int,
    height: int,
    channel_order: Sequence[int],
    scalar_type: type[_S],
    byte_order: Optional[ByteOrder] = None,
) -> npt.NDArray[_S]:
    num_channels = len(channel_order)
    shape = (height, width, num_channels)

    dtype = np.dtype(scalar_type)
    if byte_order is not None:
        dtype = dtype.newbyteorder(byte_order)

    ndarray: npt.NDArray[_S] = np.ndarray(shape=shape, dtype=dtype, buffer=image)
    ndarray = ndarray[..., channel_order]
    return ndarray.copy()


def s3tc_bytes_to_ndarray(
    encoded_image: bytes,
    logical_width: int,
    logical_height: int,
    scalar_type: type[_S],
    *,
    mode: str,
    n: int,
    pixel_format: str,
) -> npt.NDArray[_S]:
    # reference for "n" and "pixel_format": Pillow/src/PIL/DdsImagePlugin.py
    pil_image = PIL.Image.frombytes(  # pyright: ignore [reportUnknownMemberType]
        mode, (logical_width, logical_height), encoded_image, "bcn", n, pixel_format
    )

    ndarray: npt.NDArray[_S] = np.array(pil_image, dtype=scalar_type)
    ndarray = ndarray[(...,) + tuple([np.newaxis] * (3 - ndarray.ndim))]
    return ndarray.copy()


@deprecated("Use raw_bytes_to_ndarray instead")
def image_bytes_to_ndarray(  # type: ignore[misc]
    image: bytes,
    width: int,
    height: int,
    channel_order: Sequence[int],
    scalar_type: type[_S],
    byte_order: Optional[ByteOrder] = None,
) -> npt.NDArray[_S]:
    return raw_bytes_to_ndarray(image, width, height, channel_order, scalar_type, byte_order)

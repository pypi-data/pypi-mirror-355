# SPDX-FileCopyrightText: b5327157 <b5327157@protonmail.com>
#
# SPDX-License-Identifier: LGPL-3.0-or-later

from typing import Literal

import numpy as np

from typing_extensions import deprecated

from no_vtf.core.image import ImageWithRawData

from .s3tc import decode_dxt1_rgb as _decode_dxt1_rgb
from .s3tc import decode_dxt1_rgba as _decode_dxt1_rgba
from .s3tc import decode_dxt3 as _decode_dxt3
from .s3tc import decode_dxt5 as _decode_dxt5


@deprecated("Use s3tc.decode_dxt1_rgb instead")
def decode_dxt1_rgb(
    encoded_image: bytes, logical_width: int, logical_height: int
) -> ImageWithRawData[np.uint8, Literal["rgb"]]:
    return _decode_dxt1_rgb(encoded_image, logical_width, logical_height)


@deprecated("Use s3tc.decode_dxt1_rgba instead")
def decode_dxt1_rgba(
    encoded_image: bytes, logical_width: int, logical_height: int
) -> ImageWithRawData[np.uint8, Literal["rgba"]]:
    return _decode_dxt1_rgba(encoded_image, logical_width, logical_height)


@deprecated("Use s3tc.decode_dxt3 instead")
def decode_dxt3(
    encoded_image: bytes, logical_width: int, logical_height: int
) -> ImageWithRawData[np.uint8, Literal["rgba"]]:
    return _decode_dxt3(encoded_image, logical_width, logical_height)


@deprecated("Use s3tc.decode_dxt5 instead")
def decode_dxt5(
    encoded_image: bytes, logical_width: int, logical_height: int
) -> ImageWithRawData[np.uint8, Literal["rgba"]]:
    return _decode_dxt5(encoded_image, logical_width, logical_height)

# SPDX-FileCopyrightText: b5327157 <b5327157@protonmail.com>
#
# SPDX-License-Identifier: LGPL-3.0-or-later

from collections.abc import Sequence
from typing import TypeVar

import numpy as np
import numpy.typing as npt

from no_vtf.core.image import Image, ImageChannels, ImageDataTypes, ImageDataTypesLDR
from no_vtf.functional import Deferred
from no_vtf.typing import mypyc_attr

from .modifier import ImageModifier

_Id_contra = TypeVar("_Id_contra", bound=ImageDataTypes, contravariant=True)

_Ic = TypeVar("_Ic", bound=ImageChannels)


@mypyc_attr(allow_interpreted_subclasses=True)
class HdrToLdrModifier(ImageModifier[_Id_contra, _Ic, ImageDataTypesLDR, _Ic]):
    def __call__(self, image: Image[_Id_contra, _Ic]) -> Image[ImageDataTypesLDR, _Ic]:
        if Image.is_ldr(image):  # pyright: ignore [reportUnknownMemberType]
            return image  # pyright: ignore [reportUnknownVariableType]

        dtype = np.dtype(np.uint8)
        dtype_info = np.iinfo(dtype)

        data = (
            Deferred(image.data)
            .map(lambda data: data.astype(np.dtype(np.float64)))
            .map(lambda data: self._color_space_convert(data, image.channels))
            .map(lambda data: dtype_info.max * data)
            .map(lambda data: np.round(data))
            .map(lambda data: np.clip(data, dtype_info.min, dtype_info.max))
            .map(lambda data: data.astype(dtype))
        )

        return Image(data=data, dtype=dtype, channels=image.channels)

    @staticmethod
    def _color_space_convert(
        data: npt.NDArray[np.float64], channels: ImageChannels
    ) -> npt.NDArray[np.float64]:
        # this assumes the RGB/L channels always contain data in the sRGB color space
        # (i.e. there is no Du/Dv floating point data stored in there, for example)
        converted_channel_indices: Sequence[int] = ()
        match (channels):
            case "rgb" | "rgba":
                converted_channel_indices = (0, 1, 2)
            case "l" | "la":
                converted_channel_indices = (0,)
            case "a":
                pass

        if converted_channel_indices:
            converted_data = _eotf_inverse_sRGB(data[..., converted_channel_indices])
            data[..., converted_channel_indices] = converted_data

        return data


def _eotf_inverse_sRGB(L: npt.NDArray[np.float64]) -> npt.NDArray[np.float64]:  # noqa: N802, N803
    V = np.where(L <= 0.0031308, L * 12.92, 1.055 * np.power(L, 1 / 2.4) - 0.055)  # noqa: N806
    return V

# SPDX-FileCopyrightText: b5327157 <b5327157@protonmail.com>
#
# SPDX-License-Identifier: LGPL-3.0-or-later

from typing import Final, Literal, Optional, TypeVar, Union

import numpy as np

from no_vtf.core.image import Image, ImageChannels, ImageDataTypes, ImageDataTypesHDR
from no_vtf.typing import mypyc_attr

from .modifier import ImageModifier

FloatingPointNumBits = Literal[16, 32]

_Id_contra = TypeVar("_Id_contra", bound=ImageDataTypes, contravariant=True)

_Ic = TypeVar("_Ic", bound=ImageChannels)


@mypyc_attr(allow_interpreted_subclasses=True)
class FPPrecisionModifier(
    ImageModifier[_Id_contra, _Ic, Union[_Id_contra, ImageDataTypesHDR], _Ic]
):
    def __init__(
        self,
        *,
        min: Optional[FloatingPointNumBits] = None,  # noqa: A002
        max: Optional[FloatingPointNumBits] = None,  # noqa: A002
    ) -> None:
        if min is not None and max is not None and min > max:
            raise ValueError(f"Unordered precisions: {min = } <= {max = }")

        self._min: Final = min
        self._max: Final = max

    def __call__(
        self, image: Image[_Id_contra, _Ic]
    ) -> Image[Union[_Id_contra, ImageDataTypesHDR], _Ic]:
        if not np.issubdtype(image.dtype, np.floating):
            return image

        fp_bits = np.dtype(image.dtype).itemsize * 8

        if self._min is not None and fp_bits < self._min:
            dtype = np.dtype(f"float{self._min}")
            data = image.data.map(lambda data: data.astype(dtype))
            return Image(data=data, dtype=dtype, channels=image.channels)

        if self._max is not None and fp_bits > self._max:
            dtype = np.dtype(f"float{self._max}")
            data = image.data.map(lambda data: data.astype(dtype))
            return Image(data=data, dtype=dtype, channels=image.channels)

        return image

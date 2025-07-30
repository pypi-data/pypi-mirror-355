# SPDX-FileCopyrightText: b5327157 <b5327157@protonmail.com>
#
# SPDX-License-Identifier: LGPL-3.0-or-later

from typing import Final, Optional

from no_vtf.core.image import ImageDynamicRange
from no_vtf.core.texture import Texture, TextureIndex
from no_vtf.typing import mypyc_attr

from .generated.parser import VtfImage as VtfParserImage


@mypyc_attr(allow_interpreted_subclasses=True)
class VtfTexture(Texture):
    def __init__(
        self,
        *,
        dynamic_range: Optional[ImageDynamicRange],
        onebitalpha: Optional[bool] = None,
        eightbitalpha: Optional[bool] = None,
        width: int,
        height: int,
        mipmap: Optional[TextureIndex],
        frame: Optional[TextureIndex],
        face: Optional[TextureIndex],
        slice: Optional[TextureIndex],  # noqa: A002
        image: VtfParserImage,
    ) -> None:
        super().__init__(
            width=width,
            height=height,
            mipmap=mipmap,
            frame=frame,
            face=face,
            slice=slice,
        )

        self.dynamic_range: Final = dynamic_range
        self.onebitalpha: Final = onebitalpha
        self.eightbitalpha: Final = eightbitalpha
        self.image: Final = image

# SPDX-FileCopyrightText: b5327157 <b5327157@protonmail.com>
#
# SPDX-License-Identifier: LGPL-3.0-or-later

import contextlib
import pathlib
import re

from collections.abc import Sequence
from typing import BinaryIO, Final, Optional, Union

import kaitaistruct

from no_vtf.core.image import ImageDynamicRange
from no_vtf.core.texture import TextureIndex
from no_vtf.core.texture.extractor import TextureExtractor
from no_vtf.typing import mypyc_attr

from .generated.parser import Vtf as VtfParser
from .generated.parser import VtfHighResImage as VtfParserHighResImage
from .generated.parser import VtfImage as VtfParserImage
from .texture import VtfTexture


@mypyc_attr(allow_interpreted_subclasses=True)
class VtfExtractor(TextureExtractor[VtfTexture]):
    def __init__(self, *, low_res_img: bool = False) -> None:
        self.low_res_img: Final = low_res_img

    def __call__(self, path_or_io: Union[pathlib.Path, BinaryIO], /) -> Sequence[VtfTexture]:
        dynamic_range = None
        if isinstance(path_or_io, pathlib.Path):
            dynamic_range = self._guess_dynamic_range(path_or_io)

        context_manager: Union[BinaryIO, contextlib.AbstractContextManager[BinaryIO]] = (
            contextlib.nullcontext(path_or_io)
            if isinstance(path_or_io, BinaryIO)
            else open(path_or_io, "rb")
        )
        with context_manager as io:
            try:
                parser = VtfParser.from_io(io)
            except kaitaistruct.KaitaiStructError as exception:
                raise ValueError(f"Parser error: {exception}")

            if not self.low_res_img:
                high_res_img = self._high_res_image_7_0(parser) or self._high_res_image_7_3(parser)
                if not high_res_img:
                    raise ValueError("No high-resolution image found")

                textures = self._textures_from_high_res_image(parser, high_res_img, dynamic_range)
                return textures
            else:
                low_res_img = self._low_res_image_7_0(parser) or self._low_res_image_7_3(parser)
                if not low_res_img:
                    raise ValueError("No low-resolution image found")

                textures = self._textures_from_low_res_image(parser, low_res_img)
                return textures

    _hdr_file_name_pattern: Final[re.Pattern[str]] = re.compile(
        r"[_\.] \d*? hdr .*? \.vtf $", re.ASCII | re.IGNORECASE | re.VERBOSE
    )

    def _guess_dynamic_range(self, path: pathlib.Path) -> ImageDynamicRange:
        if self._hdr_file_name_pattern.search(path.name) is not None:
            return "hdr"

        return "ldr"

    def _high_res_image_7_0(self, parser: VtfParser) -> Optional[VtfParserHighResImage]:
        return getattr(parser.body, "high_res_image", None)

    def _high_res_image_7_3(self, parser: VtfParser) -> Optional[VtfParserHighResImage]:
        resources = getattr(parser.body, "resources", None)
        if not resources:
            return None

        for resource in resources:
            high_res_image: Optional[VtfParserHighResImage] = getattr(
                resource, "high_res_image", None
            )
            if high_res_image:
                return high_res_image

        return None

    def _low_res_image_7_0(self, parser: VtfParser) -> Optional[VtfParserImage]:
        return getattr(parser.body, "low_res_image", None)

    def _low_res_image_7_3(self, parser: VtfParser) -> Optional[VtfParserImage]:
        resources = getattr(parser.body, "resources", None)
        if not resources:
            return None

        for resource in resources:
            low_res_image: Optional[VtfParserImage] = getattr(resource, "low_res_image", None)
            if low_res_image:
                return low_res_image

        return None

    def _textures_from_high_res_image(
        self,
        parser: VtfParser,
        high_res_image: VtfParserHighResImage,
        dynamic_range: Optional[ImageDynamicRange],
    ) -> list[VtfTexture]:
        num_mipmaps = parser.header.v7_0.num_mipmaps
        num_frames = parser.header.v7_0.num_frames
        num_faces = parser.header.logical.num_faces
        num_slices = parser.header.logical.num_slices

        onebitalpha = parser.header.logical.flags.onebitalpha
        eightbitalpha = parser.header.logical.flags.eightbitalpha

        textures = []
        for mipmap_index, mipmap in enumerate(high_res_image.image_mipmaps):
            for frame_index, frame in enumerate(mipmap.image_frames):
                for face_index, face in enumerate(frame.image_faces):
                    for slice_index, image_slice in enumerate(face.image_slices):
                        texture = VtfTexture(
                            width=image_slice.logical_width,
                            height=image_slice.logical_height,
                            dynamic_range=dynamic_range,
                            onebitalpha=onebitalpha,
                            eightbitalpha=eightbitalpha,
                            mipmap=TextureIndex(mipmap_index, count=num_mipmaps),
                            frame=TextureIndex(frame_index, count=num_frames),
                            face=TextureIndex(face_index, count=num_faces),
                            slice=TextureIndex(slice_index, count=num_slices),
                            image=image_slice,
                        )
                        textures.append(texture)

        return textures

    def _textures_from_low_res_image(
        self, parser: VtfParser, low_res_image: VtfParserImage
    ) -> list[VtfTexture]:
        onebitalpha = parser.header.logical.flags.onebitalpha
        eightbitalpha = parser.header.logical.flags.eightbitalpha

        texture = VtfTexture(
            width=low_res_image.logical_width,
            height=low_res_image.logical_height,
            dynamic_range="ldr",
            onebitalpha=onebitalpha,
            eightbitalpha=eightbitalpha,
            mipmap=None,
            frame=None,
            face=None,
            slice=None,
            image=low_res_image,
        )
        return [texture]

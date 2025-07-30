# SPDX-FileCopyrightText: b5327157 <b5327157@protonmail.com>
#
# SPDX-License-Identifier: LGPL-3.0-or-later

import functools

from typing import Final, Optional

from no_vtf.core.image import AnyImageWithRawData, ImageDynamicRange
from no_vtf.core.image.decoder import ImageDecoder
from no_vtf.core.image.decoder.raw import (
    decode_a8,
    decode_abgr8888,
    decode_argb8888,
    decode_bgr565,
    decode_bgr888,
    decode_bgra4444,
    decode_bgra5551,
    decode_bgra8888,
    decode_bgrx5551,
    decode_bgrx8888,
    decode_l8,
    decode_la88,
    decode_rgb565,
    decode_rgb888,
    decode_rgba8888,
    decode_rgba16161616f_le,
    decode_uv88,
    decode_uvlx8888,
    decode_uvwq8888,
)
from no_vtf.core.image.decoder.s3tc import (
    decode_ati2n,
    decode_bc4,
    decode_bc7,
    decode_dxt1_rgb,
    decode_dxt1_rgba,
    decode_dxt3,
    decode_dxt5,
)
from no_vtf.core.texture.decoder import TextureDecoder
from no_vtf.typing import mypyc_attr

from .generated.parser import VtfImageFormat as VtfParserImageFormat
from .image_decoder import (
    decode_bgr888_bluescreen,
    decode_bgra8888_hdr,
    decode_rgb888_bluescreen,
    decode_rgba16161616_le_hdr,
)
from .texture import VtfTexture


@mypyc_attr(allow_interpreted_subclasses=True)
class VtfDecoder(TextureDecoder[VtfTexture, AnyImageWithRawData]):
    def __init__(
        self,
        *,
        dynamic_range: Optional[ImageDynamicRange] = None,
        overbright_factor: Optional[float] = None,
    ) -> None:
        self.dynamic_range: Final = dynamic_range
        self.overbright_factor: Final = overbright_factor

    def __call__(self, texture: VtfTexture) -> AnyImageWithRawData:
        decoder = self._get_decoder(texture)
        decoded_image = decoder(texture.image.image_data, texture.width, texture.height)
        return decoded_image

    def _get_decoder(self, texture: VtfTexture) -> ImageDecoder[AnyImageWithRawData]:
        image_format = texture.image.image_format

        dynamic_range = (
            self.dynamic_range if self.dynamic_range is not None else texture.dynamic_range
        )
        has_alpha_flag = texture.onebitalpha or texture.eightbitalpha

        decoder: Optional[ImageDecoder[AnyImageWithRawData]] = None
        match (image_format, dynamic_range, has_alpha_flag):
            case VtfParserImageFormat.rgba8888, _, _:
                decoder = decode_rgba8888
            case VtfParserImageFormat.abgr8888, _, _:
                decoder = decode_abgr8888
            case VtfParserImageFormat.rgb888, _, _:
                decoder = decode_rgb888
            case VtfParserImageFormat.bgr888, _, _:
                decoder = decode_bgr888
            case VtfParserImageFormat.rgb565, _, _:
                decoder = decode_rgb565
            case VtfParserImageFormat.i8, _, _:
                decoder = decode_l8
            case VtfParserImageFormat.ia88, _, _:
                decoder = decode_la88
            case VtfParserImageFormat.a8, _, _:
                decoder = decode_a8
            case VtfParserImageFormat.rgb888_bluescreen, _, _:
                decoder = decode_rgb888_bluescreen
            case VtfParserImageFormat.bgr888_bluescreen, _, _:
                decoder = decode_bgr888_bluescreen
            case VtfParserImageFormat.argb8888, _, _:
                # VTFLib/VTFEdit, Gimp VTF Plugin, and possibly others, decode this format
                # differently because of mismatched channels (verified against VTF2TGA).
                decoder = decode_argb8888
            case VtfParserImageFormat.bgra8888, None, _:
                raise RuntimeError("Dynamic range is set neither on VtfTexture nor VtfDecoder")
            case VtfParserImageFormat.bgra8888, "ldr", _:
                decoder = decode_bgra8888
            case VtfParserImageFormat.bgra8888, "hdr", _:
                decoder = functools.partial(
                    decode_bgra8888_hdr, overbright_factor=self.overbright_factor
                )
            case VtfParserImageFormat.dxt1, _, False:
                decoder = decode_dxt1_rgb
            case VtfParserImageFormat.dxt1, _, True:
                decoder = decode_dxt1_rgba
            case VtfParserImageFormat.dxt3, _, _:
                decoder = decode_dxt3
            case VtfParserImageFormat.dxt5, _, _:
                decoder = decode_dxt5
            case VtfParserImageFormat.bgrx8888, _, False:
                decoder = decode_bgrx8888
            case VtfParserImageFormat.bgrx8888, _, True:
                decoder = decode_bgra8888
            case VtfParserImageFormat.bgr565, _, _:
                decoder = decode_bgr565
            case VtfParserImageFormat.bgrx5551, _, False:
                decoder = decode_bgrx5551
            case VtfParserImageFormat.bgrx5551, _, True:
                decoder = decode_bgra5551
            case VtfParserImageFormat.bgra4444, _, _:
                decoder = decode_bgra4444
            case VtfParserImageFormat.dxt1_onebitalpha, _, _:
                decoder = decode_dxt1_rgba
            case VtfParserImageFormat.bgra5551, _, _:
                decoder = decode_bgra5551
            case VtfParserImageFormat.uv88, _, _:
                decoder = decode_uv88
            case VtfParserImageFormat.uvwq8888, _, _:
                decoder = decode_uvwq8888
            case VtfParserImageFormat.rgba16161616f, _, _:
                decoder = decode_rgba16161616f_le
            case VtfParserImageFormat.rgba16161616, _, _:
                decoder = decode_rgba16161616_le_hdr
            case VtfParserImageFormat.uvlx8888, _, False:
                decoder = decode_uvlx8888
            case VtfParserImageFormat.uvlx8888, _, True:
                decoder = decode_uvwq8888
            case VtfParserImageFormat.strata_source_ati2n, _, _:
                decoder = decode_ati2n
            case VtfParserImageFormat.strata_source_ati1n, _, _:
                decoder = decode_bc4
            case VtfParserImageFormat.strata_source_bc7, _, _:
                decoder = decode_bc7
            case _:
                pass

        if not decoder:
            raise NotImplementedError(f"Unsupported Valve texture format: {image_format.name}")

        return decoder

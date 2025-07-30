# SPDX-FileCopyrightText: b5327157 <b5327157@protonmail.com>
#
# SPDX-License-Identifier: LGPL-3.0-or-later

from typing import Final

from no_vtf.core.texture.namer import TextureNamer
from no_vtf.typing import mypyc_attr

from .texture import VtfTexture


@mypyc_attr(allow_interpreted_subclasses=True)
class Vtf2TgaLikeNamer(TextureNamer[VtfTexture]):
    def __init__(self, *, include_mipmap_level: bool, include_frame: bool = True) -> None:
        self.include_mipmap_level: Final = include_mipmap_level
        self.include_frame: Final = include_frame

    def __call__(self, texture: VtfTexture, *, input_name: str, **kwargs: object) -> str:
        output_name = input_name

        if texture.face and texture.face.count >= 6:
            face_names = ("rt", "lf", "bk", "ft", "up", "dn", "sph")
            output_name += face_names[texture.face.index]

        if self.include_frame and texture.frame and texture.frame.count > 1:
            output_name += f"{texture.frame.index:03d}"

        if self.include_mipmap_level and texture.mipmap and texture.mipmap.count > 1:
            mipmap_level = texture.mipmap.count - texture.mipmap.index - 1
            output_name += f"_mip{mipmap_level}"

        if texture.slice and texture.slice.count > 1:
            output_name += f"_z{texture.slice.index:03d}"

        return output_name

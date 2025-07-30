# SPDX-FileCopyrightText: b5327157 <b5327157@protonmail.com>
#
# SPDX-License-Identifier: LGPL-3.0-or-later

from typing import Final, Literal, Optional, Union

from no_vtf.core.texture import Texture, TextureIndex
from no_vtf.typing import mypyc_attr

from .texture_index import TextureIndexFilter


@mypyc_attr(allow_interpreted_subclasses=True)
class SliceFilter(TextureIndexFilter[Texture]):
    def __init__(
        self,
        *,
        slices: slice,
        last: Union[Literal["original"], Literal["filtered"]] = "original",
        strict: bool = False,
    ) -> None:
        super().__init__(slice=slices, last=last, strict=strict)

        self.slices: Final = slices

    def select_texture_index(self, texture: Texture) -> Optional[TextureIndex]:
        return texture.slice

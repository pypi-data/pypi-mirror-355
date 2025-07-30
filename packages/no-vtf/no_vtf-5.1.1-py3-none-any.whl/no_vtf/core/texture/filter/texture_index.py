# SPDX-FileCopyrightText: b5327157 <b5327157@protonmail.com>
#
# SPDX-License-Identifier: LGPL-3.0-or-later

from abc import abstractmethod
from collections.abc import Sequence
from typing import Final, Literal, Optional, TypeVar, Union

from no_vtf.core.texture import Texture, TextureIndex
from no_vtf.typing import mypyc_attr

from .filter import TextureFilter

_T_contra = TypeVar("_T_contra", bound=Texture, contravariant=True)


@mypyc_attr(allow_interpreted_subclasses=True)
class TextureIndexFilter(TextureFilter[_T_contra]):
    def __init__(
        self,
        *,
        slice: slice,  # noqa: A002
        last: Union[Literal["original"], Literal["filtered"]] = "original",
        strict: bool = False,
    ) -> None:
        self.slice: Final = slice
        self.last: Final = last
        self.strict: Final = strict

    @abstractmethod
    def select_texture_index(self, texture: _T_contra) -> Optional[TextureIndex]: ...

    def __call__(self, textures: Sequence[_T_contra]) -> Sequence[_T_contra]:
        if not textures:
            return []

        texture_index_counts = {
            texture_index.count
            for texture in textures
            if (texture_index := self.select_texture_index(texture))
        }
        if not texture_index_counts:
            return [] if self.strict else textures

        length: int
        if self.last == "original":
            if len(texture_index_counts) != 1:
                filter_type_prefix = type(self).__name__.removesuffix("Filter")
                raise ValueError(
                    f"{filter_type_prefix} count must be the same for all filtered textures"
                )

            length = next(iter(texture_index_counts))
        else:
            length = (
                max(
                    texture_index.index
                    for texture in textures
                    if (texture_index := self.select_texture_index(texture))
                )
                + 1
            )

        indices = range(*self.slice.indices(length))

        textures_filtered: list[_T_contra] = []
        for index in indices:
            textures_filtered.extend(
                texture
                for texture in textures
                if (
                    (texture_index := self.select_texture_index(texture))
                    and texture_index.index == index
                )
                or (not self.strict and not texture_index)
            )
        return textures_filtered

# SPDX-FileCopyrightText: b5327157 <b5327157@protonmail.com>
#
# SPDX-License-Identifier: LGPL-3.0-or-later

import itertools

from abc import abstractmethod
from collections.abc import Sequence
from typing import Final, Generic, TypeVar

from no_vtf.core.texture import Texture
from no_vtf.typing import mypyc_attr

_T_contra = TypeVar("_T_contra", bound=Texture, contravariant=True)


@mypyc_attr(allow_interpreted_subclasses=True)
class TextureFilter(Generic[_T_contra]):
    @abstractmethod
    def __call__(self, textures: Sequence[_T_contra]) -> Sequence[_T_contra]: ...


@mypyc_attr(allow_interpreted_subclasses=True)
class TextureCombinedFilter(TextureFilter[_T_contra]):
    def __init__(self, filters: Sequence[TextureFilter[_T_contra]]) -> None:
        self.filters: Final = filters

    def __call__(self, textures: Sequence[_T_contra]) -> Sequence[_T_contra]:
        for texture_filter in self.filters:
            textures = texture_filter(textures)

        return textures


@mypyc_attr(allow_interpreted_subclasses=True)
class TextureConcatenatedFilter(TextureFilter[_T_contra]):
    def __init__(self, filters: Sequence[TextureFilter[_T_contra]]) -> None:
        self.filters: Final = filters

    def __call__(self, textures: Sequence[_T_contra]) -> Sequence[_T_contra]:
        return list(
            itertools.chain.from_iterable(
                texture_filter(textures) for texture_filter in self.filters
            )
        )

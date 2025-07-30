# SPDX-FileCopyrightText: b5327157 <b5327157@protonmail.com>
#
# SPDX-License-Identifier: LGPL-3.0-or-later

from collections.abc import Sequence
from typing import Final, Optional

from no_vtf.core.texture import Texture
from no_vtf.typing import mypyc_attr

from .filter import TextureFilter


@mypyc_attr(allow_interpreted_subclasses=True)
class ResolutionFilter(TextureFilter[Texture]):
    def __init__(
        self,
        *,
        min: Optional[int] = None,  # noqa: A002
        max: Optional[int] = None,  # noqa: A002
        closest_as_fallback: bool = False,
    ) -> None:
        if min is not None and max is not None and min > max:
            raise ValueError(f"Unordered resolutions: {min = } <= {max = }")

        self.closest_as_fallback: Final = closest_as_fallback

        self._min: Final = min
        self._max: Final = max

    def __call__(self, textures: Sequence[Texture]) -> Sequence[Texture]:
        if self._min is self._max is None:
            return textures

        def resolution_filter(texture: Texture) -> bool:
            if self._min is not None:
                if not all(
                    resolution >= self._min for resolution in (texture.width, texture.height)
                ):
                    return False

            if self._max is not None:
                if not all(
                    resolution <= self._max for resolution in (texture.width, texture.height)
                ):
                    return False

            return True

        exact_matches = list(filter(resolution_filter, textures))
        if exact_matches or not self.closest_as_fallback:
            return exact_matches

        num_pixels = (self._min or self._max or 0) * (self._max or self._min or 0)

        close_matches = {
            abs(num_pixels - texture.width * texture.height): texture for texture in textures
        }
        close_matches = dict(sorted(close_matches.items()))

        closest_match = list(close_matches.values())[0:1]
        return closest_match

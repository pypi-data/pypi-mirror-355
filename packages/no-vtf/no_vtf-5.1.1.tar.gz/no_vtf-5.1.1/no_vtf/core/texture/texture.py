# SPDX-FileCopyrightText: b5327157 <b5327157@protonmail.com>
#
# SPDX-License-Identifier: LGPL-3.0-or-later

from __future__ import annotations

from typing import Final, Optional

from no_vtf.typing import mypyc_attr


@mypyc_attr(allow_interpreted_subclasses=True)
class Texture:
    def __init__(
        self,
        *,
        width: int,
        height: int,
        mipmap: Optional[TextureIndex],
        frame: Optional[TextureIndex],
        face: Optional[TextureIndex],
        slice: Optional[TextureIndex],  # noqa: A002
    ) -> None:
        self.width: Final = width
        self.height: Final = height

        self.mipmap: Final = mipmap
        self.frame: Final = frame
        self.face: Final = face
        self.slice: Final = slice


@mypyc_attr(allow_interpreted_subclasses=True)
class TextureIndex:
    def __init__(
        self,
        index: int,
        *,
        count: int,
    ) -> None:
        self.index: Final = index
        self.count: Final = count

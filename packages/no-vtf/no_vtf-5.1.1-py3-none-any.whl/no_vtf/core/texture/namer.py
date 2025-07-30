# SPDX-FileCopyrightText: b5327157 <b5327157@protonmail.com>
#
# SPDX-License-Identifier: LGPL-3.0-or-later

from abc import abstractmethod
from typing import Generic, TypeVar

from no_vtf.typing import mypyc_attr

from .texture import Texture

_T_contra = TypeVar("_T_contra", bound=Texture, contravariant=True)


@mypyc_attr(allow_interpreted_subclasses=True)
class TextureNamer(Generic[_T_contra]):
    @abstractmethod
    def __call__(self, texture: _T_contra, *, input_name: str, **kwargs: object) -> str: ...

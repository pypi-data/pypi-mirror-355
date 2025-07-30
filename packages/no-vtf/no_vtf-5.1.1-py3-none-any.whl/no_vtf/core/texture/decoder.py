# SPDX-FileCopyrightText: b5327157 <b5327157@protonmail.com>
#
# SPDX-License-Identifier: LGPL-3.0-or-later

from abc import abstractmethod
from typing import Generic, TypeVar

from no_vtf.core.image import AnyImageWithRawData
from no_vtf.typing import mypyc_attr

from .texture import Texture

_I_co = TypeVar("_I_co", bound=AnyImageWithRawData, covariant=True)
_T_contra = TypeVar("_T_contra", bound=Texture, contravariant=True)


@mypyc_attr(allow_interpreted_subclasses=True)
class TextureDecoder(Generic[_T_contra, _I_co]):
    @abstractmethod
    def __call__(self, texture: _T_contra) -> _I_co: ...

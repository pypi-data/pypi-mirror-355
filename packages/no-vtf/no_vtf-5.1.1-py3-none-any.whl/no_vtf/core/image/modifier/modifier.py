# SPDX-FileCopyrightText: b5327157 <b5327157@protonmail.com>
#
# SPDX-License-Identifier: LGPL-3.0-or-later

from abc import abstractmethod
from typing import Generic, TypeVar

from no_vtf.core.image import Image, ImageChannels, ImageDataTypes
from no_vtf.typing import mypyc_attr

_Id_co = TypeVar("_Id_co", bound=ImageDataTypes, covariant=True)
_Ic_co = TypeVar("_Ic_co", bound=ImageChannels, covariant=True)

_Id_contra = TypeVar("_Id_contra", bound=ImageDataTypes, contravariant=True)
_Ic_contra = TypeVar("_Ic_contra", bound=ImageChannels, contravariant=True)


@mypyc_attr(allow_interpreted_subclasses=True)
class ImageModifier(Generic[_Id_contra, _Ic_contra, _Id_co, _Ic_co]):
    @abstractmethod
    def __call__(self, image: Image[_Id_contra, _Ic_contra]) -> Image[_Id_co, _Ic_co]: ...

# SPDX-FileCopyrightText: b5327157 <b5327157@protonmail.com>
#
# SPDX-License-Identifier: GPL-3.0-only

from __future__ import annotations

import functools
import itertools
import pathlib
import re

from collections.abc import Sequence
from typing import Any, ClassVar, Final, Literal, Optional, Protocol, TypeAlias, TypeVar, cast

import imageio.core.v3_plugin_api
import imageio.plugins.freeimage
import imageio.typing
import imageio.v3
import numpy as np
import numpy.typing as npt

from typing_extensions import Self

from no_vtf.core.image import AnyImage, ImageChannels, ImageDataTypes
from no_vtf.core.image.modifier.fp_precision_modifier import FPPrecisionModifier
from no_vtf.typing import mypyc_attr

from .file import FileIO, FileIOReadbackOptions, FileIOWriteOptions
from .io import IOReadbackOptions, IOWriteOptions

_IMAGE_IO_FORMAT_PATTERN: Final[re.Pattern[str]] = re.compile(
    r"[a-z0-9]+", re.ASCII | re.IGNORECASE
)

_T_contra = TypeVar("_T_contra", bound=pathlib.Path, contravariant=True)
_I_contra = TypeVar("_I_contra", bound=AnyImage, contravariant=True)


@mypyc_attr(allow_interpreted_subclasses=True)
class ImageIOWriteOptions(FileIOWriteOptions):
    def __init__(self, copy: Optional[IOWriteOptions] = None, /) -> None:
        self.compress: Optional[bool] = None
        self.fps: Optional[int] = None

        super().__init__(copy)

    def merge(self, other: IOWriteOptions, /, *, non_none: bool = True) -> Self:
        if isinstance(other, ImageIOWriteOptions):
            self.compress = self.rightmost(self.compress, other.compress, non_none=non_none)
            self.fps = self.rightmost(self.fps, other.fps, non_none=non_none)

        return super().merge(other, non_none=non_none)


@mypyc_attr(allow_interpreted_subclasses=True)
class ImageIOReadbackOptions(FileIOReadbackOptions):
    pass


@mypyc_attr(allow_interpreted_subclasses=True)
class ImageIO(FileIO[_T_contra, _I_contra]):
    @classmethod
    def initialize(
        cls, formats: Optional[Sequence[str]] = None, *, _recursive: bool = True
    ) -> None:
        super().initialize(_recursive=False)

        if not formats:
            _ImageIOBackend.initialize()
        else:
            for backend_format in map(str.lower, formats):
                match backend_format:
                    case "apng":
                        _ImageIOApngBackend.initialize()
                    case "exr":
                        _ImageIOExrBackend.initialize()
                    case "png":
                        _ImageIOPngBackend.initialize()
                    case "targa" | "tga":
                        _ImageIOTgaBackend.initialize()
                    case "tiff":
                        _ImageIOTiffBackend.initialize()
                    case _:
                        _ImageIOBackend.initialize()

        if _recursive:
            for subclass in cls.__subclasses__():
                subclass.initialize(formats)

    def __init__(self, *, image_io_format: str, **kwargs: Any) -> None:
        super().__init__(**kwargs)

        self.image_io_format: Final = image_io_format

        if not _IMAGE_IO_FORMAT_PATTERN.fullmatch(self.image_io_format):
            raise ValueError(f"Invalid format: {self.image_io_format}")

        backend: _ImageIOBackend
        write_defaults = ImageIOWriteOptions(self.write_defaults)
        match self.image_io_format.lower():
            case "apng":
                backend = _ImageIOApngBackend()
            case "exr":
                write_defaults.fps = None
                backend = _ImageIOExrBackend()
            case "png":
                write_defaults.fps = None
                backend = _ImageIOPngBackend()
            case "targa" | "tga":
                write_defaults.fps = None
                backend = _ImageIOTgaBackend()
            case "tiff":
                write_defaults.fps = None
                backend = _ImageIOTiffBackend()
            case _:
                write_defaults.fps = None
                write_defaults.compress = None
                extension = f".{self.image_io_format}"
                backend = _ImageIOBackend(extension=extension)
        self._backend: Final = backend
        self._write_defaults.merge(write_defaults, non_none=False)

    def write_file(
        self,
        path: _T_contra,
        /,
        *images: _I_contra,
        options: IOWriteOptions = IOWriteOptions(),
    ) -> bool:
        if not super().write_file(path, *images, options=options):
            return False

        merged_options = ImageIOWriteOptions(self.write_defaults).merge(options)
        self._backend.write(path, images, merged_options)
        return True

    def readback_file(
        self,
        path: _T_contra,
        /,
        *images: _I_contra,
        options: IOReadbackOptions = IOReadbackOptions(),
    ) -> bool:
        if not super().readback_file(path, *images, options=options):
            return False

        merged_options = ImageIOReadbackOptions(self.readback_defaults).merge(options)
        self._backend.readback(path, images, merged_options)
        return True


AnyImageIO: TypeAlias = ImageIO[pathlib.Path, AnyImage]


@mypyc_attr(allow_interpreted_subclasses=True)
class _DummyImageIO(AnyImageIO):  # pyright: ignore [reportUnusedClass]
    pass


class _Opener(Protocol):
    def __call__(
        self,
        uri: imageio.typing.ImageResource,
        io_mode: Literal["r", "w"],
        *,
        extension: Optional[str] = None,
        format_hint: Optional[str] = None,
    ) -> imageio.core.v3_plugin_api.PluginV3: ...


@mypyc_attr(allow_interpreted_subclasses=True)
class _ImageIOBackend:
    @classmethod
    def initialize(cls, *, _recursive: bool = True) -> None:
        if _recursive:
            for subclass in cls.__subclasses__():
                subclass.initialize()

    def __init__(self, *, extension: Optional[str] = None) -> None:
        self._extension: Final = extension

    def write(
        self,
        path: pathlib.Path,
        sequence: Sequence[AnyImage],
        options: ImageIOWriteOptions,
    ) -> None:
        opener = self._get_opener()
        with opener(path, "w", extension=self._extension) as image_resource:
            for image in sequence:
                kwargs = self._get_writer_kwargs(image, options)
                image = self._postprocess(image)
                data = self._get_data(image)

                image_resource.write(data, **kwargs)

    def readback(
        self,
        path: pathlib.Path,
        sequence: Sequence[AnyImage],
        options: ImageIOReadbackOptions,
    ) -> None:
        opener = self._get_opener()
        with opener(path, "r", extension=self._extension) as image_resource:
            image_resource_iter = (  # pyright: ignore [reportUnknownVariableType]
                image_resource.iter()  # pyright: ignore [reportUnknownMemberType]
            )
            for (
                image,
                read_data,  # pyright: ignore [reportUnknownVariableType]
            ) in itertools.zip_longest(  # pyright: ignore [reportUnknownVariableType]
                sequence, image_resource_iter  # pyright: ignore [reportUnknownArgumentType]
            ):
                if image is None or read_data is None:
                    raise ValueError(f"{path!r}: Number of frames differs from what is in the file")

                image = self._postprocess(image)
                data = self._get_data(image)

                if data.dtype != read_data.dtype:  # pyright: ignore [reportUnknownMemberType]
                    raise ValueError(f"{path!r}: Data type differs from what is in the file")

                if not self._compare_data(
                    data, read_data  # pyright: ignore [reportUnknownArgumentType]
                ):
                    raise ValueError(f"{path!r}: Data differs from what is in the file")

    def _get_opener(self) -> _Opener:
        return cast(_Opener, imageio.v3.imopen)  # pyright: ignore [reportUnknownMemberType]

    def _get_writer_kwargs(
        self, image: AnyImage, options: ImageIOWriteOptions
    ) -> dict[str, object]:
        return {}

    def _postprocess(self, image: AnyImage) -> AnyImage:
        return image

    def _get_data(self, image: AnyImage) -> npt.NDArray[np.generic]:
        data = image.data()

        # write luminance into three channels when alpha is present
        if image.channels == "la":
            l8: npt.NDArray[ImageDataTypes] = data[:, :, [0]]
            a8: npt.NDArray[ImageDataTypes] = data[:, :, [1]]
            data = np.dstack((l8, l8, l8, a8))

        # remove last axis if its length is 1
        if data.shape[-1] == 1:
            data = data[..., 0]

        return data

    def _compare_data(
        self, data: npt.NDArray[np.generic], read_data: npt.NDArray[np.generic]
    ) -> bool:
        return np.array_equal(data, read_data)


_FP_FORCE_32_BITS: Final[FPPrecisionModifier[ImageDataTypes, ImageChannels]] = FPPrecisionModifier(
    min=32, max=32
)


@mypyc_attr(allow_interpreted_subclasses=True)
class _ImageIOPillowBackend(_ImageIOBackend):
    def __init__(self, *, extension: Optional[str] = None) -> None:
        super().__init__(extension=extension)

    def _get_opener(self) -> _Opener:
        # imopen is incorrectly typed
        return functools.partial(  # pyright: ignore [reportReturnType]
            imageio.v3.imopen, plugin="pillow"  # pyright: ignore [reportUnknownMemberType]
        )  # pyright: ignore [reportGeneralTypeIssues]


@mypyc_attr(allow_interpreted_subclasses=True)
class _ImageIOPngBackend(_ImageIOPillowBackend):
    def __init__(self, *, extension: str = ".png") -> None:
        super().__init__(extension=extension)

    def _get_writer_kwargs(
        self, image: AnyImage, options: ImageIOWriteOptions
    ) -> dict[str, object]:
        kwargs = super()._get_writer_kwargs(image, options)
        compress = options.rightmost(True, options.compress)
        if not compress:
            kwargs["compress_level"] = 0
        return kwargs


@mypyc_attr(allow_interpreted_subclasses=True)
class _ImageIOApngBackend(_ImageIOPngBackend):
    def __init__(self) -> None:
        super().__init__(extension=".apng")

    def _get_writer_kwargs(
        self, image: AnyImage, options: ImageIOWriteOptions
    ) -> dict[str, object]:
        kwargs = super()._get_writer_kwargs(image, options)
        if options.fps:
            kwargs["duration"] = 1000 / options.fps
        return kwargs


@mypyc_attr(allow_interpreted_subclasses=True)
class _ImageIOLegacyBackend(_ImageIOBackend):
    def __init__(
        self, *, imageio_format: Optional[str] = None, extension: Optional[str] = None
    ) -> None:
        super().__init__(extension=extension)
        self._imageio_format: Final = imageio_format

    def _get_opener(self) -> _Opener:
        # imopen is incorrectly typed
        return functools.partial(  # pyright: ignore [reportCallIssue]
            imageio.v3.imopen,  # pyright: ignore [reportUnknownMemberType]
            legacy_mode=True,
            plugin=self._imageio_format,
        )  # pyright: ignore [reportGeneralTypeIssues]


# IO_FLAGS is an implicit reexport
_FREEIMAGE_IO_FLAGS: Final[
    type[imageio.plugins.freeimage.IO_FLAGS]  # pyright: ignore [reportPrivateImportUsage]
] = imageio.plugins.freeimage.IO_FLAGS  # pyright: ignore [reportPrivateImportUsage]


@mypyc_attr(allow_interpreted_subclasses=True)
class _ImageIOFreeImageBackend(_ImageIOLegacyBackend):
    _freeimage_initialized: ClassVar[bool] = False

    @classmethod
    def initialize(cls, *, _recursive: bool = True) -> None:
        super().initialize(_recursive=False)

        if not _ImageIOFreeImageBackend._freeimage_initialized:
            # download() seems to be untyped because of implicit reexport
            imageio.plugins.freeimage.download()  # type: ignore[no-untyped-call]
            _ImageIOFreeImageBackend._freeimage_initialized = True

        if _recursive:
            for subclass in cls.__subclasses__():
                subclass.initialize()

    def __init__(self, *, imageio_format: str, extension: str) -> None:
        super().__init__(imageio_format=imageio_format, extension=extension)

        if not _ImageIOFreeImageBackend._freeimage_initialized:
            raise RuntimeError("ImageIO FreeImage backend was not initialized")

    def _get_writer_kwargs(
        self, image: AnyImage, options: ImageIOWriteOptions
    ) -> dict[str, object]:
        kwargs = super()._get_writer_kwargs(image, options)
        kwargs["flags"] = self._get_flags(image, options)
        return kwargs

    def _get_flags(self, image: AnyImage, options: ImageIOWriteOptions) -> int:
        return 0


@mypyc_attr(allow_interpreted_subclasses=True)
class _ImageIOExrBackend(_ImageIOFreeImageBackend):
    def __init__(self) -> None:
        super().__init__(imageio_format="EXR-FI", extension=".exr")

    def _get_flags(self, image: AnyImage, options: ImageIOWriteOptions) -> int:
        flags = super()._get_flags(image, options)
        compress = options.rightmost(True, options.compress)
        flags |= _FREEIMAGE_IO_FLAGS.EXR_ZIP if compress else _FREEIMAGE_IO_FLAGS.EXR_NONE
        if not np.issubdtype(image.data().dtype, np.float16):
            flags |= _FREEIMAGE_IO_FLAGS.EXR_FLOAT
        return flags

    def _postprocess(self, image: AnyImage) -> AnyImage:
        return _FP_FORCE_32_BITS(image)


@mypyc_attr(allow_interpreted_subclasses=True)
class _ImageIOTgaBackend(_ImageIOFreeImageBackend):
    def __init__(self) -> None:
        super().__init__(imageio_format="TARGA-FI", extension=".tga")

    def _get_flags(self, image: AnyImage, options: ImageIOWriteOptions) -> int:
        flags = super()._get_flags(image, options)
        compress = options.rightmost(True, options.compress)
        flags |= (
            _FREEIMAGE_IO_FLAGS.TARGA_SAVE_RLE if compress else _FREEIMAGE_IO_FLAGS.TARGA_DEFAULT
        )
        return flags


@mypyc_attr(allow_interpreted_subclasses=True)
class _ImageIOTiffBackend(_ImageIOFreeImageBackend):
    def __init__(self) -> None:
        super().__init__(imageio_format="TIFF-FI", extension=".tiff")

    def _get_flags(self, image: AnyImage, options: ImageIOWriteOptions) -> int:
        flags = super()._get_flags(image, options)
        compress = options.rightmost(True, options.compress)
        flags |= _FREEIMAGE_IO_FLAGS.TIFF_DEFAULT if compress else _FREEIMAGE_IO_FLAGS.TIFF_NONE
        return flags

    def _postprocess(self, image: AnyImage) -> AnyImage:
        return _FP_FORCE_32_BITS(image)

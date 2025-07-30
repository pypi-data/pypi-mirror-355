# SPDX-FileCopyrightText: b5327157 <b5327157@protonmail.com>
#
# SPDX-License-Identifier: GPL-3.0-only

from __future__ import annotations

import collections
import functools
import pathlib
import re

from abc import abstractmethod
from collections import defaultdict
from collections.abc import Callable, Mapping, Sequence
from typing import Final, Generic, Literal, Optional, Protocol, TypeAlias, TypeVar, overload

from no_vtf.typing import mypyc_attr

from .image import AnyImage, AnyImageWithRawData, ImageChannels, ImageDataTypes, ImageDynamicRange
from .image.channel_separator import ChannelSeparator
from .image.io.file import FileIO, FileIOWriteOptions
from .image.io.image import AnyImageIO
from .image.io.raw import AnyRawIO
from .image.modifier import ImageModifier
from .texture import Texture
from .texture.decoder import TextureDecoder
from .texture.extractor import TextureExtractor
from .texture.filter import TextureFilter
from .texture.namer import TextureNamer

Quantity = Literal["single", "multi"]

ImageIOMapping: TypeAlias = Mapping[tuple[Quantity, ImageDynamicRange], AnyImageIO]

_T_contra = TypeVar("_T_contra", bound=Texture, contravariant=True)

_I = TypeVar("_I", bound=AnyImage)
_I_co = TypeVar("_I_co", bound=AnyImage, covariant=True)
_I2_co = TypeVar("_I2_co", bound=AnyImage, covariant=True)


@mypyc_attr(allow_interpreted_subclasses=True)
class Receipt:
    def __init__(self) -> None:
        self.io_ready = False
        self.io_done = False
        self.output_written: Final[collections.Counter[pathlib.Path]] = collections.Counter()


@mypyc_attr(allow_interpreted_subclasses=True)
class Pipeline(Generic[_T_contra]):
    def __init__(
        self,
        *,
        input_extension_pattern: Optional[re.Pattern[str]] = None,
        animate: bool = False,
        separate_channels: bool = False,
        extractor: TextureExtractor[_T_contra],
        filter: Optional[TextureFilter[_T_contra]],  # noqa: A002
        decoder: TextureDecoder[_T_contra, AnyImageWithRawData],
        modifiers: Optional[
            Sequence[ImageModifier[ImageDataTypes, ImageChannels, ImageDataTypes, ImageChannels]]
        ] = None,
        namer: TextureNamer[_T_contra],
        image_io_write: Optional[ImageIOMapping] = None,
        image_io_readback: Optional[ImageIOMapping] = None,
        raw_io_write: Optional[AnyRawIO] = None,
        raw_io_readback: Optional[AnyRawIO] = None,
    ) -> None:
        self._input_extension_pattern: Final = input_extension_pattern

        self._animate: Final = animate
        self._separate_channels: Final = separate_channels

        self._extractor: Final = extractor
        self._filter: Final = filter
        self._decoder: Final = decoder
        self._namer: Final = namer

        self._image_io_write: Final = image_io_write or {}
        self._image_io_readback: Final = image_io_readback or {}

        self._raw_io_write: Final = raw_io_write
        self._raw_io_readback: Final = raw_io_readback

        self._apply_modifiers: Final = (
            functools.partial(_apply_modifiers, modifiers=modifiers) if modifiers else None
        )

    @overload
    def __call__(
        self,
        input_file: pathlib.Path,
        /,
        *,
        output_file: pathlib.Path,
        receipt: Optional[Receipt] = None,
    ) -> Receipt: ...

    @overload
    def __call__(
        self,
        input_file: pathlib.Path,
        /,
        *,
        output_directory: pathlib.Path,
        receipt: Optional[Receipt] = None,
    ) -> Receipt: ...

    def __call__(
        self,
        input_file: pathlib.Path,
        /,
        *,
        output_file: Optional[pathlib.Path] = None,
        output_directory: Optional[pathlib.Path] = None,
        receipt: Optional[Receipt] = None,
    ) -> Receipt:
        receipt = receipt or Receipt()

        items = self._get_items(input_file)

        if self._image_io_write or self._image_io_readback:
            self._process_items_image(items, receipt, output_file, output_directory)

        if self._raw_io_write or self._raw_io_readback:
            self._process_items_raw(items, receipt, output_file, output_directory)

        return receipt

    def _get_items(self, input_file: pathlib.Path) -> Sequence[_PipelineItem[AnyImageWithRawData]]:
        textures = self._extractor(input_file)

        if self._filter:
            textures = self._filter(textures)

        items: list[_PipelineItem[AnyImageWithRawData]] = []
        for texture in textures:
            image: AnyImageWithRawData = self._decoder(texture)

            input_name = input_file.name
            if self._input_extension_pattern:
                input_name = re.sub(self._input_extension_pattern, "", input_name)

            output_stem = self._namer(texture, input_name=input_name)

            item = _PipelineItem(sequence=[image], output_stem=output_stem)
            items.append(item)

        return items

    def _process_items_image(
        self,
        items: Sequence[_PipelineItem[AnyImage]],
        receipt: Receipt,
        output_file: Optional[pathlib.Path] = None,
        output_directory: Optional[pathlib.Path] = None,
    ) -> Receipt:
        do_write_io = _DoImageIO(self._image_io_write, output_file, output_directory, receipt)
        do_readback_io = _DoImageIO(self._image_io_readback, output_file, output_directory, receipt)

        steps: Sequence[Optional[_PipelineStep[AnyImage]]] = [
            self._apply_modifiers,
            _separate_channels if self._separate_channels else None,
            _group_by_output_stem if self._animate else None,
            do_write_io.write_step,
            do_readback_io.readback_step,
        ]
        for step in steps:
            if step:
                items = step(items)

        return receipt

    def _process_items_raw(
        self,
        items: Sequence[_PipelineItem[AnyImageWithRawData]],
        receipt: Receipt,
        output_file: Optional[pathlib.Path] = None,
        output_directory: Optional[pathlib.Path] = None,
    ) -> Receipt:
        do_write_io = _DoRawIO(self._raw_io_write, output_file, output_directory, receipt)
        do_readback_io = _DoRawIO(self._raw_io_readback, output_file, output_directory, receipt)

        steps: Sequence[Optional[_PipelineStep[AnyImageWithRawData]]] = [
            _group_by_output_stem if self._animate else None,
            do_write_io.write_step,
            do_readback_io.readback_step,
        ]
        for step in steps:
            if step:
                items = step(items)

        return receipt


@mypyc_attr(allow_interpreted_subclasses=True)
class _PipelineItem(Generic[_I_co]):
    def __init__(self, *, sequence: Sequence[_I_co], output_stem: str) -> None:
        self.sequence: Final = sequence
        self.output_stem: Final = output_stem


class _PipelineStep(Protocol[_I]):
    def __call__(self, items: Sequence[_PipelineItem[_I]]) -> Sequence[_PipelineItem[_I]]: ...


def _apply_modifiers(
    items: Sequence[_PipelineItem[AnyImage]],
    *,
    modifiers: Sequence[
        ImageModifier[ImageDataTypes, ImageChannels, ImageDataTypes, ImageChannels]
    ],
) -> Sequence[_PipelineItem[AnyImage]]:
    def apply_modifier(
        image: AnyImage,
        modifier: ImageModifier[ImageDataTypes, ImageChannels, ImageDataTypes, ImageChannels],
    ) -> AnyImage:
        return modifier(image)

    return [
        _PipelineItem(
            sequence=[
                functools.reduce(apply_modifier, modifiers, image) for image in item.sequence
            ],
            output_stem=item.output_stem,
        )
        for item in items
    ]


def _separate_channels(
    items: Sequence[_PipelineItem[AnyImage]],
    *,
    channel_separator: ChannelSeparator = ChannelSeparator(),
) -> Sequence[_PipelineItem[AnyImage]]:
    new_items: list[_PipelineItem[AnyImage]] = []
    for item in items:
        new_sequence_by_channels: defaultdict[str, list[AnyImage]] = defaultdict(list)
        for image in item.sequence:
            for image_seperated in channel_separator(image):
                new_sequence_by_channels[image_seperated.channels].append(image_seperated)

        for channels, new_sequence in new_sequence_by_channels.items():
            new_output_stem = f"{item.output_stem}_{channels}"
            new_item = _PipelineItem(sequence=new_sequence, output_stem=new_output_stem)
            new_items.append(new_item)

    return new_items


def _group_by_output_stem(items: Sequence[_PipelineItem[_I]]) -> Sequence[_PipelineItem[_I]]:
    item_by_output_stem: dict[str, _PipelineItem[_I]] = {}
    for item in items:
        output_stem = item.output_stem
        if output_stem not in item_by_output_stem:
            item_by_output_stem[output_stem] = item
        else:
            old_item = item_by_output_stem[output_stem]
            new_sequence = list(old_item.sequence) + list(item.sequence)
            new_item = _PipelineItem(sequence=new_sequence, output_stem=output_stem)
            item_by_output_stem[output_stem] = new_item

    return list(item_by_output_stem.values())


@mypyc_attr(allow_interpreted_subclasses=True)
class _DoIO(Generic[_I]):
    def __init__(
        self,
        output_file: Optional[pathlib.Path],
        output_directory: Optional[pathlib.Path],
        receipt: Receipt,
    ) -> None:
        self.output_file: Final = output_file
        self.output_directory: Final = output_directory
        self.receipt: Final = receipt

    def write_step(self, items: Sequence[_PipelineItem[_I]]) -> Sequence[_PipelineItem[_I]]:
        return self._do_io_operations(items, self._write_io_operation)

    def readback_step(self, items: Sequence[_PipelineItem[_I]]) -> Sequence[_PipelineItem[_I]]:
        return self._do_io_operations(items, self._readback_io_operation)

    def _do_io_operations(
        self,
        items: Sequence[_PipelineItem[_I]],
        io_operation: Callable[[_PipelineItem[_I], FileIO[pathlib.Path, _I], pathlib.Path], bool],
    ) -> Sequence[_PipelineItem[_I]]:
        for item in items:
            io = self._get_io(item)
            output_file_path = self._get_output_file_path(item)
            if io and output_file_path:
                self.receipt.io_ready = True
                if io_operation(item, io, output_file_path):
                    self.receipt.io_done = True

        return items

    def _write_io_operation(
        self,
        item: _PipelineItem[_I],
        io: FileIO[pathlib.Path, _I],
        output_file_path: pathlib.Path,
    ) -> bool:
        options = FileIOWriteOptions()
        options.mkdir_parents = True

        if self.receipt.output_written[output_file_path]:
            options.overwrite = True

        if not io.write_file(output_file_path, *item.sequence, options=options):
            return False

        self.receipt.output_written[output_file_path] += 1
        return True

    def _readback_io_operation(
        self,
        item: _PipelineItem[_I],
        io: FileIO[pathlib.Path, _I],
        output_file_path: pathlib.Path,
    ) -> bool:
        return io.readback_file(output_file_path, *item.sequence)

    def _get_output_file_path(self, item: _PipelineItem[_I]) -> Optional[pathlib.Path]:
        if self.output_file:
            return self.output_file

        output_path_extension = self._get_output_path_extension(item)
        if not output_path_extension:
            return None

        output_name = f"{item.output_stem}.{output_path_extension}"

        assert self.output_directory  # noqa S101 type narrowing
        return self.output_directory / output_name

    @abstractmethod
    def _get_io(self, item: _PipelineItem[_I]) -> Optional[FileIO[pathlib.Path, _I]]: ...

    @abstractmethod
    def _get_output_path_extension(self, item: _PipelineItem[_I]) -> Optional[str]: ...


@mypyc_attr(allow_interpreted_subclasses=True)
class _DoRawIO(_DoIO[AnyImageWithRawData]):
    def __init__(
        self,
        raw_io: Optional[AnyRawIO],
        output_file: Optional[pathlib.Path],
        output_directory: Optional[pathlib.Path],
        receipt: Receipt,
    ) -> None:
        super().__init__(output_file, output_directory, receipt)
        self.raw_io: Final = raw_io

    def _get_io(self, item: _PipelineItem[_I]) -> Optional[AnyRawIO]:
        return self.raw_io

    def _get_output_path_extension(self, item: _PipelineItem[_I]) -> str:
        return "raw"


@mypyc_attr(allow_interpreted_subclasses=True)
class _DoImageIO(_DoIO[AnyImage]):
    def __init__(
        self,
        image_io_mapping: ImageIOMapping,
        output_file: Optional[pathlib.Path],
        output_directory: Optional[pathlib.Path],
        receipt: Receipt,
    ) -> None:
        super().__init__(output_file, output_directory, receipt)
        self.image_io_mapping: Final = image_io_mapping

    def _get_io(self, item: _PipelineItem[AnyImage]) -> Optional[AnyImageIO]:
        if not item.sequence:
            return None

        quantity: Quantity = "multi" if len(item.sequence) > 1 else "single"
        dynamic_range = item.sequence[0].dynamic_range

        for image in item.sequence:
            if image.dynamic_range != dynamic_range:
                raise ValueError("Dynamic range must be the same for all images")

        return self.image_io_mapping.get((quantity, dynamic_range))

    def _get_output_path_extension(self, item: _PipelineItem[_I]) -> Optional[str]:
        io = self._get_io(item)
        return io.image_io_format if io else None

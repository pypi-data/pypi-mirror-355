# SPDX-FileCopyrightText: b5327157 <b5327157@protonmail.com>
#
# SPDX-License-Identifier: GPL-3.0-only

from __future__ import annotations

import contextlib
import functools
import pathlib
import re
import sys
import traceback

from collections.abc import Callable, Sequence
from typing import Final, Generic, Literal, Optional, TypedDict, TypeVar, Union, cast, overload

import click

from ._alive_progress import alive_bar
from ._click import apply_param_default, error, posix_tty_style, sanitize, warning
from .core.image import ImageChannels, ImageDataTypes, ImageDynamicRange
from .core.image.io.file import FileIOWriteOptions
from .core.image.io.image import AnyImageIO, ImageIO, ImageIOWriteOptions
from .core.image.io.raw import AnyRawIO, RawIOWriteOptions
from .core.image.modifier import ImageModifier
from .core.image.modifier.hdr_to_ldr_modifier import HdrToLdrModifier
from .core.pipeline import ImageIOMapping, Pipeline, Quantity, Receipt
from .core.texture import Texture
from .core.texture.filter import (
    FaceFilter,
    FrameFilter,
    MipmapFilter,
    ResolutionFilter,
    SliceFilter,
    TextureCombinedFilter,
    TextureConcatenatedFilter,
    TextureFilter,
)
from .filesystem import InputPaths, OutputDirectories
from .task_runner import ParallelRunner, SequentialRunner, TaskRunner
from .vtf import Vtf2TgaLikeNamer, VtfDecoder, VtfExtractor, VtfTexture

_T = TypeVar("_T", bound=Texture)
_T_co = TypeVar("_T_co", bound=Texture, covariant=True)

_FORMAT_SKIP: Final[Literal["skip"]] = "skip"


class _PipelineIO(TypedDict, total=False):
    image_io_write: Optional[ImageIOMapping]
    image_io_readback: Optional[ImageIOMapping]
    raw_io_write: Optional[AnyRawIO]
    raw_io_readback: Optional[AnyRawIO]


def main(
    *,
    paths: Sequence[pathlib.Path],
    output_directory: Optional[pathlib.Path] = None,
    output_file: Optional[pathlib.Path] = None,
    ldr_format: Optional[str] = None,
    hdr_format: Optional[str] = None,
    dynamic_range: Optional[ImageDynamicRange] = None,
    mipmaps: Optional[bool] = None,
    min_resolution: Optional[int] = None,
    max_resolution: Optional[int] = None,
    closest_resolution: Optional[bool] = None,
    frames: Optional[Union[Sequence[slice], slice]] = None,
    faces: Optional[Union[Sequence[slice], slice]] = None,
    slices: Optional[Union[Sequence[slice], slice]] = None,
    animate: Optional[bool] = None,
    fps: Optional[int] = None,
    separate_channels: Optional[bool] = None,
    overbright_factor: Optional[float] = None,
    hdr_to_ldr: Optional[bool] = None,
    low_res_img: Optional[bool] = None,
    compress: Optional[bool] = None,
    raw: Optional[bool] = None,
    write: Optional[bool] = None,
    readback: Optional[bool] = None,
    num_workers: Optional[int] = None,
    no_progress: Optional[bool] = None,
) -> None:
    from .main import main_command

    if output_file and output_directory:
        raise ValueError("Output file and directory is mutually exclusive")

    params = main_command.params
    ldr_format = apply_param_default(params, "ldr_format", str, ldr_format)
    hdr_format = apply_param_default(params, "hdr_format", str, hdr_format)
    mipmaps = apply_param_default(params, "mipmaps", bool, mipmaps)
    closest_resolution = apply_param_default(params, "closest_resolution", bool, closest_resolution)
    animate = apply_param_default(params, "animate", bool, animate)
    fps = apply_param_default(params, "fps", int, fps)
    separate_channels = apply_param_default(params, "separate_channels", bool, separate_channels)
    overbright_factor = apply_param_default(params, "overbright_factor", float, overbright_factor)
    hdr_to_ldr = apply_param_default(params, "hdr_to_ldr", bool, hdr_to_ldr)
    low_res_img = apply_param_default(params, "low_res_img", bool, low_res_img)
    raw = apply_param_default(params, "raw", bool, raw)
    readback = apply_param_default(params, "readback", bool, readback)
    no_progress = apply_param_default(params, "no_progress", bool, no_progress)

    vtf_extension_pattern = re.compile(r"\.vtf$", re.ASCII | re.IGNORECASE)

    frames = [frames] if isinstance(frames, slice) else frames
    faces = [faces] if isinstance(faces, slice) else faces
    slices = [slices] if isinstance(slices, slice) else slices

    texture_filters = _get_filters(
        mipmaps=mipmaps,
        min_resolution=min_resolution,
        max_resolution=max_resolution,
        closest_resolution=closest_resolution,
        frames=frames,
        faces=faces,
        slices=slices,
    )

    texture_extractor = VtfExtractor(low_res_img=low_res_img)
    texture_filter = TextureCombinedFilter(texture_filters)
    texture_decoder = VtfDecoder(dynamic_range=dynamic_range, overbright_factor=overbright_factor)
    texture_namer = Vtf2TgaLikeNamer(include_mipmap_level=mipmaps, include_frame=(not animate))

    modifiers: list[ImageModifier[ImageDataTypes, ImageChannels, ImageDataTypes, ImageChannels]] = (
        []
    )
    if hdr_to_ldr:
        modifiers.append(HdrToLdrModifier())

    pipeline_io, io_initializer = _create_io(
        write=write,
        readback=readback,
        raw=raw,
        ldr_format=ldr_format,
        hdr_format=hdr_format,
        compress=compress,
        fps=fps,
    )

    pipeline = Pipeline(
        input_extension_pattern=vtf_extension_pattern,
        animate=animate,
        separate_channels=separate_channels,
        extractor=texture_extractor,
        filter=texture_filter,
        decoder=texture_decoder,
        modifiers=modifiers,
        namer=texture_namer,
        **pipeline_io,
    )

    input_paths = InputPaths(paths)
    if input_paths.has_directories():
        _resolve_directories(input_paths, not no_progress)

    if output_file:
        tasks = _get_tasks(pipeline, input_paths, output_file=output_file)
    else:
        tasks = _get_tasks(pipeline, input_paths, output_directory=output_directory)

    task_runner: TaskRunner
    if (num_workers is None and len(tasks) > 1) or (num_workers and num_workers > 1):
        task_runner = ParallelRunner(max_workers=num_workers, initializer=io_initializer)
    else:
        task_runner = SequentialRunner()

    exit_status, io_ready, io_done = _process_tasks(task_runner, tasks, not no_progress)

    if write is None and not readback and tasks and exit_status == 0 and io_ready and not io_done:
        message = (
            "No file was written. Did you mean to use the "
            + click.style("--always-write", bold=True)
            + " option?"
        )
        warning(message)

    sys.exit(exit_status)


def _get_filters(
    *,
    mipmaps: bool,
    min_resolution: Optional[int],
    max_resolution: Optional[int],
    closest_resolution: bool,
    frames: Optional[Sequence[slice]],
    faces: Optional[Sequence[slice]],
    slices: Optional[Sequence[slice]],
) -> Sequence[TextureFilter[VtfTexture]]:
    texture_filters: list[TextureFilter[VtfTexture]] = []

    if frames:
        texture_filters.append(
            TextureConcatenatedFilter([FrameFilter(frames=frame_slice) for frame_slice in frames])
        )
    if faces:
        texture_filters.append(
            TextureConcatenatedFilter([FaceFilter(faces=face_slice) for face_slice in faces])
        )
    if slices:
        texture_filters.append(
            TextureConcatenatedFilter([SliceFilter(slices=slice_slice) for slice_slice in slices])
        )
    if min_resolution is not None or max_resolution is not None:
        texture_filters.append(
            ResolutionFilter(
                min=min_resolution, max=max_resolution, closest_as_fallback=closest_resolution
            )
        )
    if not mipmaps:
        texture_filters.append(MipmapFilter(mipmap_levels=slice(-1, None), last="filtered"))

    return texture_filters


def _create_io(
    *,
    write: Optional[bool],
    readback: bool,
    raw: bool,
    ldr_format: str,
    hdr_format: str,
    compress: Optional[bool],
    fps: Optional[int],
) -> tuple[_PipelineIO, Optional[Callable[[], None]]]:
    base_write_defaults = FileIOWriteOptions()
    base_write_defaults.overwrite = write is True

    pipeline_io = _PipelineIO()
    io_initializer: Optional[Callable[[], None]] = None
    if not raw:
        ldr_format_split = ldr_format.split("|")
        hdr_format_split = hdr_format.split("|")

        non_skip_formats = [
            format_ for format_ in ldr_format_split + hdr_format_split if format_ != _FORMAT_SKIP
        ]
        io_initializer = functools.partial(ImageIO.initialize, non_skip_formats)
        io_initializer()

        ldr_format_single: Final = ldr_format_split[0]
        hdr_format_single: Final = hdr_format_split[0]

        ldr_format_multi: Final = (ldr_format_split[1:2] or ldr_format_split[0:1])[0]
        hdr_format_multi: Final = (hdr_format_split[1:2] or hdr_format_split[0:1])[0]

        image_io_write_defaults = ImageIOWriteOptions().merge(base_write_defaults)
        image_io_write_defaults.fps = fps
        image_io_write_defaults.compress = compress

        image_io: dict[tuple[Quantity, ImageDynamicRange], AnyImageIO] = {}
        if image_io_ldr_single := _create_image_io(ldr_format_single, image_io_write_defaults):
            image_io["single", "ldr"] = image_io_ldr_single
        if image_io_hdr_single := _create_image_io(hdr_format_single, image_io_write_defaults):
            image_io["single", "hdr"] = image_io_hdr_single
        if image_io_ldr_multi := _create_image_io(ldr_format_multi, image_io_write_defaults):
            image_io["multi", "ldr"] = image_io_ldr_multi
        if image_io_hdr_multi := _create_image_io(hdr_format_multi, image_io_write_defaults):
            image_io["multi", "hdr"] = image_io_hdr_multi

        pipeline_io["image_io_write"] = image_io if write is not False else None
        pipeline_io["image_io_readback"] = image_io if readback else None
    else:
        raw_io_write_defaults = RawIOWriteOptions().merge(base_write_defaults)
        raw_io = AnyRawIO(write_defaults=raw_io_write_defaults)

        pipeline_io["raw_io_write"] = raw_io if write is not False else None
        pipeline_io["raw_io_readback"] = raw_io if readback else None

    return pipeline_io, io_initializer


def _create_image_io(
    output_format: str,
    write_defaults: ImageIOWriteOptions,
    *,
    _unhandled_compression_formats: list[str] = [],
) -> Optional[AnyImageIO]:
    if output_format == _FORMAT_SKIP:
        return None

    image_io = AnyImageIO(image_io_format=output_format, write_defaults=write_defaults)

    if (
        write_defaults.compress is not None
        and ImageIOWriteOptions(image_io.write_defaults).compress is None
        and output_format not in _unhandled_compression_formats
    ):
        message = (
            "Format "
            + click.style(image_io.image_io_format, bold=True)
            + " does not support compression control."
        )
        warning(message)

        _unhandled_compression_formats.append(image_io.image_io_format)

    return image_io


def _resolve_directories(input_paths: InputPaths, show_progress: bool) -> None:
    progress_bar_manager = alive_bar(receipt=False) if show_progress else None
    with progress_bar_manager or contextlib.nullcontext() as progress_bar:
        for file in input_paths.search_in_directories("*.[vV][tT][fF]", add_results=True):
            if progress_bar:
                progress_bar.text = posix_tty_style(sanitize(file.name), io=sys.stderr, bold=True)
                progress_bar()
        input_paths.remove_directories()


@overload
def _get_tasks(
    pipeline: Pipeline[_T], input_paths: InputPaths, *, output_directory: Optional[pathlib.Path]
) -> Sequence[_Task[_T]]: ...


@overload
def _get_tasks(
    pipeline: Pipeline[_T], input_paths: InputPaths, *, output_file: pathlib.Path
) -> Sequence[_Task[_T]]: ...


def _get_tasks(  # pyright: ignore [reportInconsistentOverload]
    pipeline: Pipeline[_T],
    input_paths: InputPaths,
    *,
    output_directory: Optional[pathlib.Path] = None,
    output_file: Optional[pathlib.Path] = None,
) -> Sequence[_Task[_T]]:
    output_directories = OutputDirectories(output_directory)

    tasks: list[_Task[_T]] = []
    for input_file, input_base_directory in input_paths:
        if output_file:
            task = _Task(pipeline=pipeline, input_file=input_file, output_file=output_file)
        else:
            output_directory = output_directories(input_file, input_base_directory)
            task = _Task(
                pipeline=pipeline, input_file=input_file, output_directory=output_directory
            )
        tasks.append(task)
    return tasks


def _process_tasks(
    task_runner: TaskRunner,
    tasks: Sequence[_Task[Texture]],
    show_progress: bool,
) -> tuple[int, bool, bool]:
    exit_status = 0
    io_ready = False
    io_done = False

    # progress bar must be run to issue the final receipt even if there are no tasks
    progress_bar_manager = alive_bar(len(tasks)) if show_progress else None
    with progress_bar_manager or contextlib.nullcontext() as progress_bar:
        overwrite_warning_shown = False

        for task, result in task_runner(tasks):
            task = cast(_Task[Texture], task)
            if isinstance(result, Receipt):
                io_ready = result.io_ready or io_ready
                io_done = result.io_done or io_done

                if (
                    any(value > 1 for value in result.output_written.values())
                    and not overwrite_warning_shown
                ):
                    message = (
                        "An output file was written to multiple times."
                        + " This can be avoided by using extraction filters."
                        + " This message will be shown only once."
                    )
                    warning(message, item=repr(task))

                    overwrite_warning_shown = True

                if progress_bar:
                    skipped = not result.io_done
                    progress_bar(skipped=skipped)
                    progress_bar.text = posix_tty_style(
                        sanitize(task.input_file.name), io=sys.stderr, bold=True
                    )
            else:
                exit_status = 1

                exception: Exception = result
                formatted_exception = "".join(traceback.format_exception(exception))
                error(formatted_exception, item=repr(task))

    return exit_status, io_ready, io_done


class _Task(Generic[_T_co]):
    @overload
    def __init__(
        self, *, pipeline: Pipeline[_T_co], input_file: pathlib.Path, output_directory: pathlib.Path
    ) -> None: ...

    @overload
    def __init__(
        self, *, pipeline: Pipeline[_T_co], input_file: pathlib.Path, output_file: pathlib.Path
    ) -> None: ...

    def __init__(
        self,
        *,
        pipeline: Pipeline[_T_co],
        input_file: pathlib.Path,
        output_directory: Optional[pathlib.Path] = None,
        output_file: Optional[pathlib.Path] = None,
    ) -> None:
        self.pipeline: Final = pipeline
        self.input_file: Final = input_file

        self._output_directory: Final = output_directory
        self._output_file: Final = output_file

    def __call__(self) -> Receipt:
        if self._output_file:
            return self.pipeline(self.input_file, output_file=self._output_file)
        else:
            assert self._output_directory  # noqa S101 type narrowing
            return self.pipeline(self.input_file, output_directory=self._output_directory)

    def __str__(self) -> str:
        return f"{self.input_file}"

    def __repr__(self) -> str:
        return f"{str(self.input_file)!r}"

# SPDX-FileCopyrightText: b5327157 <b5327157@protonmail.com>
#
# SPDX-License-Identifier: GPL-3.0-only

import inspect
import pathlib

from collections.abc import Sequence
from typing import Literal, Optional, Union

import click
import click_option_group

import no_vtf

from ._click import (
    GroupedOption,
    HelpFormatter,
    HiddenFromShellCompletionOption,
    OptionGroup,
    ShellCompletionOption,
    Slice,
    echo,
)

_ImageDynamicRange = Literal["ldr", "hdr"]


COMPLETE_VAR = "_NO_VTF_COMPLETE"


def _show_credits(ctx: click.Context, param: click.Parameter, value: bool) -> None:
    if not value or ctx.resilient_parsing:
        return

    credits = """
    no_vtf - Valve Texture Format Converter
    Copyright (C) b5327157

    https://git.sr.ht/~b5327157/no_vtf/
    https://pypi.org/project/no-vtf/
    https://developer.valvesoftware.com/wiki/no_vtf

    This program is free software: you can redistribute it and/or modify it
    under the terms of the GNU General Public License as published by the Free
    Software Foundation, version 3 only.

    This program is distributed in the hope that it will be useful, but WITHOUT
    ANY WARRANTY; without even the implied warranty of MERCHANTABILITY or FITNESS
    FOR A PARTICULAR PURPOSE. See the GNU General Public License for more details.

    You should have received a copy of the GNU General Public License along with
    this program. If not, see <https://www.gnu.org/licenses/>.
    """

    echo(inspect.cleandoc(credits))
    ctx.exit()


def _show_version(ctx: click.Context, param: click.Parameter, value: bool) -> None:
    if not value or ctx.resilient_parsing:
        return

    echo(no_vtf.__version__)
    ctx.exit()


click.Context.formatter_class = HelpFormatter


@click.command(name="no_vtf", no_args_is_help=True)
@click.argument(
    "paths",
    metavar="[--] PATH...",
    type=click.Path(path_type=pathlib.Path, exists=True),
    required=True,
    nargs=-1,
)
@click_option_group.optgroup("Conversion mode", cls=OptionGroup)  # type: ignore[misc]
@click_option_group.optgroup.option(
    "--animate/--no-animate",
    cls=GroupedOption,
    help="Output animated image file (default) / output each frame individually",
    type=bool,
    default=True,
)
@click_option_group.optgroup.option(
    "--raw",
    cls=GroupedOption,
    help="Extract image data as-is (without decoding)",
    type=bool,
    is_flag=True,
)
@click_option_group.optgroup("\n  Extraction", cls=OptionGroup)  # type: ignore[misc]
@click_option_group.optgroup.option(
    "--mipmaps",
    "-m",
    cls=GroupedOption,
    help="Extract all mipmaps",
    type=bool,
    is_flag=True,
)
@click_option_group.optgroup.option(
    "--low-res-img",
    cls=GroupedOption,
    help="Extract the low-resolution image",
    type=bool,
    is_flag=True,
)
@click_option_group.optgroup.option(
    "--min-resolution",
    cls=GroupedOption,
    help="Minimum mipmap resolution",
    metavar="INTEGER",
    type=click.IntRange(min=1),
)
@click_option_group.optgroup.option(
    "--max-resolution",
    cls=GroupedOption,
    help="Maximum mipmap resolution",
    metavar="INTEGER",
    type=click.IntRange(min=1),
)
@click_option_group.optgroup.option(
    "--closest-resolution",
    cls=GroupedOption,
    help="Fallback to the closest resolution if no exact match",
    type=bool,
    is_flag=True,
)
@click_option_group.optgroup.option(
    "--frames",
    cls=GroupedOption,
    help="Frames to extract",
    type=Slice(),
)
@click_option_group.optgroup.option(
    "--faces",
    cls=GroupedOption,
    help="Faces to extract",
    type=Slice(),
)
@click_option_group.optgroup.option(
    "--slices",
    cls=GroupedOption,
    help="Slices to extract",
    type=Slice(),
)
@click_option_group.optgroup(
    "\n  Image decoding (not used with --raw)",
    cls=OptionGroup,
)  # type: ignore[misc]
@click_option_group.optgroup.option(
    "--dynamic-range",
    cls=GroupedOption,
    help="Override LDR/HDR auto-detection",
    type=click.Choice(["ldr", "hdr"], case_sensitive=False),
)
@click_option_group.optgroup.option(
    "--overbright-factor",
    cls=GroupedOption,
    help="Multiplicative factor used for decoding compressed HDR textures",
    show_default=True,
    type=float,
    default=16.0,
)
@click_option_group.optgroup(
    "\n  Image postprocessing (not used with --raw)",
    cls=OptionGroup,
)  # type: ignore[misc]
@click_option_group.optgroup.option(
    "--hdr-to-ldr",
    cls=GroupedOption,
    help="Convert HDR from linear sRGB to sRGB and output as clipped LDR",
    type=bool,
    is_flag=True,
)
@click_option_group.optgroup.option(
    "--separate-channels",
    cls=GroupedOption,
    help="Output the RGB/L and A channels separately",
    type=bool,
    is_flag=True,
)
@click_option_group.optgroup(
    "\n  Image output (not used with --raw)",
    cls=OptionGroup,
)  # type: ignore[misc]
@click_option_group.optgroup.option(
    "--ldr-format",
    "-f",
    cls=GroupedOption,
    help="LDR output format",
    metavar="SINGLE[|MULTI]",
    show_default=True,
    type=str,
    default="tiff|apng",
)
@click_option_group.optgroup.option(
    "--hdr-format",
    "-F",
    cls=GroupedOption,
    help="HDR output format",
    metavar="SINGLE[|MULTI]",
    show_default=True,
    type=str,
    default="exr",
)
@click_option_group.optgroup.option(
    "--fps",
    cls=GroupedOption,
    help="Frame rate used for animated image files",
    show_default=True,
    type=int,
    default=5,
)
@click_option_group.optgroup.option(
    "--compress/--no-compress",
    cls=GroupedOption,
    help="Control lossless compression",
    type=bool,
    default=None,
)
@click_option_group.optgroup("\n  Read/write control", cls=OptionGroup)  # type: ignore[misc]
@click_option_group.optgroup.option(
    "write",
    "--always-write/--no-write",
    cls=GroupedOption,
    help="Write images",
    type=bool,
    default=None,
)
@click_option_group.optgroup.option(
    "readback",
    "--readback/--no-readback",
    cls=GroupedOption,
    help="Readback images",
    type=bool,
    default=False,
)
@click_option_group.optgroup("\n  Output destination", cls=OptionGroup)  # type: ignore[misc]
@click_option_group.optgroup.option(
    "--output-dir",
    "-o",
    "output_directory",
    cls=GroupedOption,
    help="Output directory",
    metavar="PATH",
    type=click.Path(path_type=pathlib.Path, exists=True, file_okay=False, dir_okay=True),
)
@click_option_group.optgroup.option(
    "--output-file",
    "-O",
    cls=GroupedOption,
    help="Output file",
    metavar="PATH",
    type=click.Path(path_type=pathlib.Path, file_okay=True, dir_okay=False),
)
@click_option_group.optgroup("\n  Miscellaneous", cls=OptionGroup)  # type: ignore[misc]
@click_option_group.optgroup.option(
    "--num-workers",
    cls=GroupedOption,
    help="Number of workers for parallel conversion",
    metavar="INTEGER",
    type=click.IntRange(min=1),
)
@click_option_group.optgroup.option(
    "--no-progress",
    cls=GroupedOption,
    help="Do not show the progress bar",
    type=bool,
    is_flag=True,
)
@click_option_group.optgroup("\n  Info", cls=OptionGroup)  # type: ignore[misc]
@click_option_group.optgroup.option(
    cls=ShellCompletionOption[GroupedOption, HiddenFromShellCompletionOption],
    complete_var=COMPLETE_VAR,
)
@click_option_group.optgroup.help_option("--help", "-h", cls=GroupedOption)
@click_option_group.optgroup.option(
    "--version",
    cls=GroupedOption,
    help="Show the version and exit.",
    type=bool,
    is_flag=True,
    expose_value=False,
    is_eager=True,
    callback=_show_version,
)
@click_option_group.optgroup.option(
    "--credits",
    cls=GroupedOption,
    help="Show the credits and exit.",
    type=bool,
    is_flag=True,
    expose_value=False,
    is_eager=True,
    callback=_show_credits,
)
def main_command(
    *,
    paths: Sequence[pathlib.Path],
    output_directory: Optional[pathlib.Path],
    output_file: Optional[pathlib.Path],
    ldr_format: str,
    hdr_format: str,
    dynamic_range: Optional[_ImageDynamicRange],
    mipmaps: bool,
    min_resolution: Optional[int],
    max_resolution: Optional[int],
    closest_resolution: bool,
    frames: Optional[Union[Sequence[slice], slice]],
    faces: Optional[Union[Sequence[slice], slice]],
    slices: Optional[Union[Sequence[slice], slice]],
    animate: bool,
    fps: int,
    separate_channels: bool,
    overbright_factor: float,
    hdr_to_ldr: bool,
    low_res_img: bool,
    compress: Optional[bool],
    raw: bool,
    write: Optional[bool],
    readback: bool,
    num_workers: Optional[int],
    no_progress: bool,
) -> None:
    """
    Convert Valve Texture Format files into standard image files.

    PATH can be either a file or a directory (in which case it is recursively searched
    for .vtf files; symbolic links are not followed). Multiple paths may be provided.

    As the output path, it is possible to specify either a file or a directory.

    Specifying the output file is useful mostly for single-file conversions,
    with filters to ensure the output file will be written only once.

    If the output directory is not specified, images are output into the source directories
    (in-place conversion). Otherwise, the directory tree for any found files will be reconstructed
    in the chosen directory.

    Output LDR/HDR format is selected by its common file name extension. It is recommended selecting
    one of the specifically supported image formats (PNG, APNG, TGA, TIFF, EXR). Other image formats
    have not been validated to work, but can still be selected. A secondary format specifically used
    to output animated image files can be selected after '|' (see default LDR format as an example).
    The "skip" format can be used to skip the R/W step entirely.

    For the specifically supported image formats, compression is configurable when saving the image.
    Lossless compression is enabled by default. Lossy compression is not used.

    The BGRA8888 format can store both LDR and compressed HDR images.
    The specific type is either auto-detected by looking at the input file name
    (roughly, if it contains "hdr" near the end), or can be set manually.

    It is possible to filter images to convert by min/max resolution (width & height),
    and by frames/faces/slices. The former supports exact or closest match. The latter
    supports selection by single index or via Python slicing:
    https://python-reference.readthedocs.io/en/latest/docs/brackets/slicing.html
    It is also possible to specify multiple indices/slices separated by commas.

    Face index mapping: right (0), left, back, front, up, down, sphere map (6).

    After applying filters, only the highest-resolution mipmap is converted by default.
    Alternatively, all mipmaps of the high-resolution image can be converted.

    Animated textures are converted into an animated multi-frame image file by default.
    Alternatively, they can also be converted into single-frame images when animation is disabled.

    The RGB/L and A channels are packed into one file by default.
    When output separately, resulting file names will be suffixed with "_rgb", "_l", or "_a".

    By default, image files are only written if they do not exist already.
    Alternatively, they can be overwritten, or writing can be disabled entirely.

    Images can also be read back to verify they have been written properly.
    Readback will error if would-be-written data does not match what is in the file.

    Workers are spawned for each logical core to run the conversion in parallel.
    The number of workers can be overridden. If set to 1, conversion is sequential.
    Sequential conversion enables more verbose errors to be printed.

    Exit status: Zero if all went successfully, non-zero if there was an error.
    Upon a recoverable error, conversion will proceed with the next file.
    """

    main(
        paths=paths,
        output_directory=output_directory,
        output_file=output_file,
        ldr_format=ldr_format,
        hdr_format=hdr_format,
        dynamic_range=dynamic_range,
        mipmaps=mipmaps,
        min_resolution=min_resolution,
        max_resolution=max_resolution,
        closest_resolution=closest_resolution,
        frames=frames,
        faces=faces,
        slices=slices,
        animate=animate,
        fps=fps,
        separate_channels=separate_channels,
        overbright_factor=overbright_factor,
        hdr_to_ldr=hdr_to_ldr,
        low_res_img=low_res_img,
        compress=compress,
        raw=raw,
        write=write,
        readback=readback,
        num_workers=num_workers,
        no_progress=no_progress,
    )


def main(
    *,
    paths: Sequence[pathlib.Path],
    output_directory: Optional[pathlib.Path] = None,
    output_file: Optional[pathlib.Path] = None,
    ldr_format: Optional[str] = None,
    hdr_format: Optional[str] = None,
    dynamic_range: Optional[_ImageDynamicRange] = None,
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
    from ._main import main

    main(
        paths=paths,
        output_directory=output_directory,
        output_file=output_file,
        ldr_format=ldr_format,
        hdr_format=hdr_format,
        dynamic_range=dynamic_range,
        mipmaps=mipmaps,
        min_resolution=min_resolution,
        max_resolution=max_resolution,
        closest_resolution=closest_resolution,
        frames=frames,
        faces=faces,
        slices=slices,
        animate=animate,
        fps=fps,
        separate_channels=separate_channels,
        overbright_factor=overbright_factor,
        hdr_to_ldr=hdr_to_ldr,
        low_res_img=low_res_img,
        compress=compress,
        raw=raw,
        write=write,
        readback=readback,
        num_workers=num_workers,
        no_progress=no_progress,
    )

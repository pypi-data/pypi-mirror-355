# SPDX-FileCopyrightText: b5327157 <b5327157@protonmail.com>
#
# SPDX-License-Identifier: LGPL-3.0-or-later

import functools
import itertools
import sys

from collections.abc import Callable, Iterator, Sequence
from contextlib import AbstractContextManager
from typing import Optional, Protocol, cast

import alive_progress
import alive_progress.animations.bars
import alive_progress.animations.spinner_compiler
import alive_progress.animations.spinners
import alive_progress.animations.utils
import alive_progress.styles.internal
import alive_progress.utils.cells
import click

from typing_extensions import ParamSpec

from ._click import posix_tty_style

_P = ParamSpec("_P")


class AliveBar(Protocol):
    text: str

    def __call__(self, *, skipped: bool = False) -> None: ...


def alive_bar(
    total: Optional[int] = None, *, receipt: bool = True
) -> AbstractContextManager[AliveBar]:
    style = functools.partial(posix_tty_style, io=sys.stderr)

    classic = bar_factory(
        style("=", fg=127, bold=True),
        tip=style(">", fg=127, bold=True),
        background=" ",
        borders=(
            style("[", fg=172, bold=True),
            style("]", fg=172, bold=True),
        ),
        underflow=style("!", fg="red", bold=True),
        overflow=style("x", fg="red", bold=True),
    )

    brackets = bouncing_spinner_factory(
        style(">" * 10, fg=127, bold=True), style("<" * 10, fg=127, bold=True)
    )

    alive_progress.styles.internal.BARS["no_vtf"] = classic
    alive_progress.styles.internal.SPINNERS["no_vtf"] = brackets

    return cast(
        AbstractContextManager[AliveBar],
        alive_progress.alive_bar(
            total,
            length=40,
            spinner=None,
            bar="no_vtf",
            unknown="no_vtf",
            file=sys.stderr,
            enrich_print=False,
            receipt=receipt,
        ),
    )


def bouncing_spinner_factory(chars_1: str, chars_2: str, *, right: bool = True) -> object:
    scroll_1 = scrolling_spinner_factory(chars_1, right=right)
    scroll_2 = scrolling_spinner_factory(chars_2, right=not right)
    return alive_progress.animations.spinners.sequential_spinner_factory(scroll_1, scroll_2)


def scrolling_spinner_factory(chars: str, *, right: bool = True) -> object:
    num_cells = len(alive_progress.utils.cells.to_cells(click.unstyle(chars)))
    natural = num_cells * 2

    @alive_progress.animations.spinner_compiler.spinner_controller(
        natural=natural,
    )  # type: ignore[misc]
    def inner_spinner_factory(actual_length: Optional[int] = None) -> object:  # type: ignore[misc]
        def frame_data() -> Iterator[str]:
            nonlocal actual_length
            actual_length = actual_length or natural

            start = 0
            stop = actual_length - num_cells + 1
            frame_iterator: Sequence[int] = list(range(start, stop))
            if not right:
                frame_iterator = list(reversed(frame_iterator))

            for i in frame_iterator:
                yield " " * i + chars + " " * (actual_length - i - num_cells)

        return (frame_data(),)

    return inner_spinner_factory


def bar_factory(  # noqa: C901
    base: str,
    *,
    tip: str,
    background: str,
    underflow: str,
    overflow: str,
    borders: Optional[tuple[str, str]] = None,
) -> object:
    @alive_progress.animations.bars.bar_controller  # type: ignore[misc]
    def inner_bar_factory(  # type: ignore[misc]
        length: int, spinner_factory: Optional[Callable[[int], object]] = None
    ) -> object:
        @bordered(borders, "||")
        def draw_known(
            running: bool, percent: float
        ) -> tuple[tuple[str, ...], Optional[tuple[str]]]:
            percent = max(0, percent)

            base_length = round(percent * (length + 1))
            tip_length = 0

            if base_length > 0:
                if base_length <= length:
                    tip_length += 1

                base_length = min(length, base_length - 1)

            underflow_length = 0
            underflow_border = False
            if not running and percent < 1:
                if base_length + tip_length < length:
                    underflow_length = 1
                else:
                    underflow_border = True

            background_length = length - (base_length + tip_length + underflow_length)

            rendered_base = base_length * (base,)
            rendered_tip = tip_length * (tip,)
            rendered_underflow = underflow_length * (underflow,)
            rendered_background = background_length * (background,)

            right_border = None
            if percent > 1:
                right_border = (overflow,)
            if underflow_border:
                right_border = (underflow,)

            return (
                rendered_base + rendered_tip + rendered_underflow + rendered_background,
                right_border,
            )

        if not spinner_factory:
            return draw_known, True, False, None

        player = alive_progress.animations.utils.spinner_player(spinner_factory(length))

        @bordered(borders, "||")
        def draw_unknown(percent: float) -> tuple[tuple[str, ...], Optional[tuple[str]]]:
            return next(player), None

        return draw_known, True, False, draw_unknown

    return inner_bar_factory


def bordered(borders: Optional[Sequence[str]], default: Sequence[str]) -> Callable[
    [Callable[_P, tuple[tuple[str, ...], Optional[tuple[str]]]]],
    Callable[_P, tuple[str, ...]],
]:
    def wrapper(
        fn: Callable[_P, tuple[tuple[str, ...], Optional[tuple[str]]]]
    ) -> Callable[_P, tuple[str, ...]]:
        @functools.wraps(fn)
        def inner_bordered(*args: _P.args, **kwargs: _P.kwargs) -> tuple[str, ...]:
            content, right = fn(*args, **kwargs)
            return tuple(itertools.chain(left_border, content, right or right_border))

        return inner_bordered

    left_border = tuple((borders or default)[0:1] or default[0:1])
    right_border = tuple((borders or default)[1:2] or default[1:2])
    return wrapper

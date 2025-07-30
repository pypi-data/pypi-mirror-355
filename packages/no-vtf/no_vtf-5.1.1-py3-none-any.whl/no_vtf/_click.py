# SPDX-FileCopyrightText: b5327157 <b5327157@protonmail.com>
#
# SPDX-License-Identifier: LGPL-3.0-or-later

from __future__ import annotations

import functools
import inspect
import os
import pathlib
import re
import shlex
import shutil
import sys

from collections.abc import Callable, Sequence
from typing import IO, Any, Final, Optional, TextIO, TypeVar, Union

import click
import click.shell_completion
import click_option_group

_AnyStr = TypeVar("_AnyStr", bytes, str)
_T = TypeVar("_T")
_F = TypeVar("_F", bound=Callable[..., Any])


def _add_ctx_arg(f: _F) -> _F:
    @functools.wraps(f)
    def wrapper(*args: Any, **kwargs: Any) -> Any:  # type: ignore[misc]
        if "ctx" not in kwargs:
            kwargs["ctx"] = click.get_current_context(silent=True)

        return f(*args, **kwargs)

    return wrapper  # type: ignore[return-value]


class _EnableDynamicInheritanceMeta(type):
    def __getitem__(cls, bases: Union[type, Sequence[type]], /) -> _EnableDynamicInheritanceMeta:
        if isinstance(bases, type):
            bases = [bases]

        bases = (cls,) + tuple(bases)
        name = f"_{'_'.join(base.__name__ for base in bases)}"
        return type(cls)(name, bases, {})


class ShellCompletionOption(click.Option, metaclass=_EnableDynamicInheritanceMeta):
    _shells: Final = {
        "bash": [
            "{prog_name} {shell_completion_opt} >> ~/.bashrc",
            "{complete_var}=bash_source {console_script}",
            '[ ! -x {console_script} ] || eval "$({complete_source})"',
            """
            if [ -x {console_script} ]; then
                {complete_var}_CACHE="${{XDG_CACHE_HOME:-${{HOME}}/.cache}}/{complete_subdir}/{shell}"
                if [ ! -e "${complete_var}_CACHE" ] || \
[ {console_script} -nt "${complete_var}_CACHE" ]; then
                    mkdir --parents "$(dirname "${complete_var}_CACHE")"
                    {complete_source} >"${complete_var}_CACHE"
                fi
                source "${complete_var}_CACHE"
                unset {complete_var}_CACHE
            fi
            """,
        ],
        "zsh": [
            "{prog_name} {shell_completion_opt} >> ~/.zshrc",
            "{complete_var}=zsh_source {console_script}",
            '[ ! -x {console_script} ] || eval "$({complete_source})"',
            """
            if [ -x {console_script} ]; then
                {complete_var}_CACHE="${{XDG_CACHE_HOME:-${{HOME}}/.cache}}/{complete_subdir}/{shell}"
                if [ ! -e "${complete_var}_CACHE" ] || \
[ {console_script} -nt "${complete_var}_CACHE" ]; then
                    mkdir --parents "$(dirname "${complete_var}_CACHE")"
                    {complete_source} >"${complete_var}_CACHE"
                fi
                source "${complete_var}_CACHE"
                unset {complete_var}_CACHE
            fi
            """,
        ],
        "fish": [
            "{prog_name} {shell_completion_opt} > ~/.config/fish/completions/{prog_name}.fish",
            "{complete_var}=fish_source {console_script}",
            '[ ! -x {console_script} ] || eval "$({complete_source})"',
            """
            if [ -x {console_script} ]
                if [ -n "$XDG_CACHE_HOME" ]
                    set {complete_var}_CACHE "$XDG_CACHE_HOME"'/{complete_subdir}/{shell}'
                else
                    set {complete_var}_CACHE "$HOME"'/.cache/{complete_subdir}/{shell}'
                end
                if [ ! -e "${complete_var}_CACHE" ] || \
[ {console_script} -nt "${complete_var}_CACHE" ]
                    mkdir --parents "$(dirname "${complete_var}_CACHE")"
                    {complete_source} >"${complete_var}_CACHE"
                end
                source "${complete_var}_CACHE"
                set -e {complete_var}_CACHE
            end
            """,
        ],
    }

    _env_var_name_pattern: Final[re.Pattern[str]] = re.compile(
        r"(?![0-9])[a-z_0-9]+", re.ASCII | re.IGNORECASE
    )

    def __init__(
        self,
        param_decls: Optional[Sequence[str]] = None,
        *,
        help: Optional[str] = None,  # noqa: A002
        hidden: bool = False,
        cache: bool = True,
        complete_var: Optional[str] = None,
        **kwargs: Any,
    ) -> None:
        if not param_decls:
            param_decls = ["--shell-completion"]

        if not help:
            help = "Setup shell completion."  # noqa: A001

        hidden = hidden or not self._is_platform_supported()

        super().__init__(
            param_decls,
            help=help,
            hidden=hidden,
            type=str,
            metavar="[SHELL]",
            is_flag=False,
            flag_value="",
            expose_value=False,
            is_eager=True,
            callback=self._callback,
            **kwargs,
        )

        self.cache: Final = cache
        self.complete_var: Final = complete_var

    def _callback(
        self, ctx: click.Context, param: click.Parameter, shell: Optional[str], /
    ) -> None:
        if shell is None or ctx.resilient_parsing:
            return

        try:
            if not self._is_platform_supported():
                raise RuntimeError("Only the Linux platform is supported")

            strict = not sys.stdout.isatty()
            io = sys.stdout if strict else sys.stderr
            echo = functools.partial(click.echo, file=io)
            style = functools.partial(posix_tty_style, io=io)

            console_script_path = self._detect_console_script_path()
            prog_name = console_script_path.name
            complete_var = self._get_complete_var(prog_name)

            shell = shell or self._detect_shell(strict=strict)
            shell = self._check_supported_shell(shell, strict=strict)

            print_shells = [
                print_shell for print_shell in self._shells if shell in {print_shell, None}
            ]
            for shell in print_shells:
                shell_desc = self._shells[shell]

                append_command = shell_desc[0].format(
                    prog_name=shlex.quote(prog_name),
                    shell_completion_opt=self.opts[0],
                )
                complete_source = shell_desc[1].format(
                    complete_var=complete_var,
                    console_script=shlex.quote(str(console_script_path)),
                )

                if not self.cache:
                    complete_command = shell_desc[2].format(
                        console_script=shlex.quote(str(console_script_path)),
                        complete_source=complete_source,
                    )
                else:
                    complete_command = (
                        inspect.cleandoc(shell_desc[3])
                        .replace(4 * " ", "\t")
                        .format(
                            console_script=shlex.quote(str(console_script_path)),
                            complete_var=complete_var,
                            complete_subdir=complete_var.removeprefix("_").lower(),
                            shell=shell,  # noqa S604 false positive
                            complete_source=complete_source,
                        )
                    )

                if not strict:
                    echo(
                        os.fsencode(
                            f"In {shell}, execute "
                            + f"{style(append_command, bold=True)}"
                            + f" to append the following {'lines' if self.cache else 'line'}:"
                        )
                    )

                echo("")
                echo(os.fsencode(complete_command))

                if not strict:
                    echo("")

            if not strict:
                echo("Finally, restart the shell to load the completion support.")

        except Exception as ex:
            error(str(ex))
            ctx.exit(1)

        ctx.exit()

    def _is_platform_supported(self) -> bool:
        return sys.platform == "linux"

    def _detect_console_script_path(self) -> pathlib.Path:
        if override := os.environ.get("_CONSOLE_SCRIPT_PATH_OVERRIDE"):
            return pathlib.Path(override)

        # click/utils.py, _detect_program_name()
        if getattr(sys.modules["__main__"], "__package__", None):
            raise RuntimeError(
                "The program must be run as a console script command, not as a module"
            )

        cmd_path = shutil.which(sys.argv[0])
        if not cmd_path:
            raise RuntimeError(f"Cannot determine command path for {sys.argv[0]!r}")

        full_path = pathlib.Path(cmd_path).resolve(strict=True)
        if full_path.name.endswith(".py"):
            raise RuntimeError(
                "The program must be run as a console script command, not as a Python script"
            )

        return full_path

    def _get_complete_var(self, prog_name: str) -> str:
        complete_var = self.complete_var

        if not complete_var:
            # click/core.py, _main_shell_completion()
            complete_name = prog_name.replace("-", "_").replace(".", "_")
            complete_var = f"_{complete_name}_COMPLETE".upper()

            if not self._env_var_name_pattern.fullmatch(complete_var):
                raise RuntimeError(
                    "Only letters, digits, and underscores are allowed in the program name"
                )

        return complete_var

    def _detect_shell(self, *, strict: bool) -> Optional[str]:
        try:
            return pathlib.Path(f"/proc/{os.getppid()}/exe").resolve(strict=True).name
        except Exception as ex:
            message = f"Cannot detect shell: {str(ex)}"

            if not strict:
                error(f"{message}\n")
                return None
            else:
                raise RuntimeError(message) from ex

    def _check_supported_shell(self, shell: Optional[str], *, strict: bool) -> Optional[str]:
        if shell and shell in self._shells:
            return shell

        if shell:
            message = (
                f"The {sanitize(shell, unsafe_extras=' ')} shell is not supported. "
                + f"Supported shells: {', '.join(self._shells)}."
            )

            if not strict:
                warning(f"{message}\n")
            else:
                raise RuntimeError(message)

        return None


class HiddenFromShellCompletionOption(click.Option):
    @property
    def hidden(self) -> bool:
        # during shell completion there is no current Click context
        if not click.get_current_context(silent=True):
            return True

        return bool(vars(self).get("hidden"))

    @hidden.setter
    def hidden(self, value: bool, /) -> None:
        vars(self)["hidden"] = value


class HelpFormatter(click.HelpFormatter):
    def write_usage(self, prog: str, args: str = "", prefix: Optional[str] = None) -> None:
        prog = click.style(prog, fg=127, bold=True)
        args = click.style(args, bold=True)
        super().write_usage(prog, args, prefix)

    def write_heading(self, heading: str) -> None:
        heading = click.style(heading, underline=True)
        super().write_heading(heading)


class OptionGroup(click_option_group.OptionGroup):
    def get_help_record(self, ctx: click.Context) -> Optional[tuple[str, str]]:
        help_record = super().get_help_record(ctx)
        if not help_record:
            return None

        name, help_ = help_record
        name = click.style(name, fg=172, bold=True)
        return name, help_


class GroupedOption(click_option_group.GroupedOption):
    _dim_pattern: Final[re.Pattern[str]] = re.compile(r"(?<=\s)\[[^\[\]\s]+\]", re.ASCII)

    def get_help_record(self, ctx: click.Context) -> Optional[tuple[str, str]]:
        help_record = super().get_help_record(ctx)
        if help_record is None:
            return None

        def dim_repl(match: re.Match[str]) -> str:
            return click.style(match.group(), dim=True)

        opts, opt_help = help_record
        opt_help = self._dim_pattern.sub(dim_repl, opt_help)
        return opts, opt_help


class Slice(click.ParamType):
    name = "slice"

    @_add_ctx_arg
    def get_metavar(self, param: click.Parameter, ctx: click.Context) -> str:
        return "INDEX|[START]:[STOP][:STEP]"

    def convert(
        self,
        value: Union[str, Sequence[slice], slice],
        param: Optional[click.Parameter],
        ctx: Optional[click.Context],
    ) -> Sequence[slice]:
        if isinstance(value, slice):
            return [value]
        if not isinstance(value, str):
            return value

        return [self._convert_single(single, param, ctx) for single in value.split(",")]

    def _convert_single(
        self,
        value: str,
        param: Optional[click.Parameter],
        ctx: Optional[click.Context],
    ) -> slice:
        slice_indices = self._to_slice_indices(value, param, ctx)

        start = slice_indices[0]
        if len(slice_indices) == 1:
            if start is None:
                self.fail("Index is empty.", param, ctx)
            if start >= 0:
                return slice(start, start + 1)
            else:
                stop = start + 1 if start != -1 else None
                return slice(start, stop)

        stop = slice_indices[1]
        if len(slice_indices) == 2:
            return slice(start, stop)

        step = slice_indices[2]
        if len(slice_indices) == 3:
            if step == 0:
                self.fail("Slice step cannot be zero.", param, ctx)
            return slice(start, stop, step)

        self.fail(f"Too many values in {value!r}.", param, ctx)

    def _to_slice_indices(
        self, value: str, param: Optional[click.Parameter], ctx: Optional[click.Context]
    ) -> list[Optional[int]]:
        slice_indices: list[Optional[int]] = []
        for slice_index in value.split(":"):
            if not slice_index:
                slice_indices.append(None)
            else:
                try:
                    slice_indices.append(int(slice_index))
                except ValueError:
                    self.fail(f"{slice_index!r} is not a valid integer.", param, ctx)
        return slice_indices


def get_param_default(
    params: Sequence[click.core.Parameter], param_name: str, param_type: type[_T]
) -> _T:
    for param in params:
        if param.name == param_name:
            default = param.default
            if callable(default):
                default = default()

            if not isinstance(default, param_type):
                raise ValueError(f"{type(default) = } {param_type = }")

            return default

    raise ValueError(f"No such parameter: {param_name}")


def apply_param_default(
    params: Sequence[click.core.Parameter],
    param_name: str,
    param_type: type[_T],
    value: Optional[_T],
) -> _T:
    return value if value is not None else get_param_default(params, param_name, param_type)


def posix_tty_style(
    text: str,
    *,
    io: TextIO,
    fg: Optional[Union[int, tuple[int, int, int], str]] = None,
    bg: Optional[Union[int, tuple[int, int, int], str]] = None,
    bold: Optional[bool] = None,
    dim: Optional[bool] = None,
    underline: Optional[bool] = None,
    overline: Optional[bool] = None,
    italic: Optional[bool] = None,
    blink: Optional[bool] = None,
    reverse: Optional[bool] = None,
    strikethrough: Optional[bool] = None,
    reset: bool = True,
) -> str:
    if os.name == "posix" and io.isatty():
        return click.style(
            text,
            fg=fg,
            bg=bg,
            bold=bold,
            dim=dim,
            underline=underline,
            overline=overline,
            italic=italic,
            blink=blink,
            reverse=reverse,
            strikethrough=strikethrough,
            reset=reset,
        )

    return text


def echo(
    message: str,
    file: Optional[IO[_AnyStr]] = None,
    nl: bool = True,
    err: bool = False,
    color: Optional[bool] = None,
) -> None:
    message = click.style("", reset=True) + message
    click.echo(message, file, nl, err, color)


def warning(
    message: str,
    *,
    item: Optional[str] = None,
) -> None:
    message = (
        click.style("Warning", fg="yellow")
        + (" while processing " + click.style(item, bold=True) if item else "")
        + ": "
        + message
    )
    echo(message, file=sys.stderr)


def error(
    message: str,
    *,
    item: Optional[str] = None,
) -> None:
    message = (
        click.style("Error", fg="red")
        + (" while processing " + click.style(item, bold=True) if item else "")
        + ": "
        + message
    )
    echo(message, file=sys.stderr)


def sanitize(string: str, /, *, unsafe_extras: Optional[Sequence[str]] = None) -> str:
    unsafe_extras = unsafe_extras or []

    if any(unsafe in string for unsafe in ["'", '"', *unsafe_extras]):
        return repr(string)

    if repr(string)[1:-1] != string:
        return repr(string)

    return string

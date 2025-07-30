# SPDX-FileCopyrightText: b5327157 <b5327157@protonmail.com>
#
# SPDX-License-Identifier: GPL-3.0-or-later

from __future__ import annotations

import contextlib
import fnmatch
import functools
import itertools
import json
import logging
import os
import pathlib
import re
import shutil
import subprocess
import sys
import sysconfig
import tempfile
import threading

from abc import abstractmethod
from collections.abc import Callable, Iterable, Iterator, Mapping, Sequence
from contextlib import AbstractContextManager, contextmanager
from dataclasses import dataclass
from typing import (
    IO,
    TYPE_CHECKING,
    Any,
    ClassVar,
    Concatenate,
    Final,
    Literal,
    Optional,
    ParamSpec,
    Protocol,
    TypeAlias,
    TypedDict,
    TypeVar,
    Union,
    final,
    overload,
)

import nox
import nox.command
import nox.logger
import nox.popen

if sys.platform == "linux":
    import fcntl
    import pty
    import termios
    import tty

if sys.version_info >= (3, 11):
    from typing import Self, Unpack
elif TYPE_CHECKING:
    from typing_extensions import Self, Unpack

StrPath: TypeAlias = Union[str, os.PathLike[str]]

_T_co = TypeVar("_T_co", covariant=True)
_T_contra = TypeVar("_T_contra", contravariant=True)

nox.needs_version = ">= 2025.5.1"

nox.options.default_venv_backend = "venv"
if sys.platform == "linux":
    nox.options.default_venv_backend = "uv|" + nox.options.default_venv_backend

nox.options.error_on_external_run = True
nox.options.error_on_missing_interpreters = True
nox.options.sessions = ["lint"]


def tag_cachedir(dir: pathlib.Path) -> None:  # noqa: A002
    dir.mkdir(parents=True, exist_ok=True)
    pathlib.Path(dir, "CACHEDIR.TAG").write_bytes(b"Signature: 8a477f597d28d172789f06886806bc55\n")


if __file__:
    tag_cachedir(pathlib.Path(__file__).parent / ".nox")


@nox.session
def lint(session: nox.Session) -> None:
    session.install("black[colorama] >= 24.10.0, < 25")
    session.install("flake8 >= 7.1.1, < 8")
    session.install("flake8-bandit >= 4.1.1, < 5")
    session.install("flake8-builtins >= 2.5.0, < 3")
    session.install("flake8-deprecated >= 2.2.1, < 3")
    session.install("flake8-pep585 >= 0.1.7, < 1")
    session.install("isort[colors] >= 5.13.2, < 6")
    session.install("mypy[faster-cache] >= 1.13.0, < 2")
    session.install("nox >= 2024.10.9, < 2025")
    session.install("pep8-naming >= 0.14.1, < 1")
    session.install("pyright >= 1.1.390, < 2")
    session.install("reuse >= 5.0.2, < 6")
    session.install("shellcheck-py >= 0.10.0.1, < 1")
    session.install("shfmt-py >= 3.7.0.1, < 4")

    session.install("types-Pillow >= 10.2.0.20240822, < 11")

    session.install(".")

    posargs_paths = session.posargs

    fix = False
    if posargs_paths and posargs_paths[0] == "--fix":
        posargs_paths = posargs_paths[1:]
        fix = True

    posargs_paths = [str(pathlib.Path(session.invoked_from, path)) for path in posargs_paths]

    default_paths = ["no_vtf", "noxfile.py", "builds", "ksy"]

    paths = [pathlib.Path(path) for path in (posargs_paths or default_paths)]
    py_paths = [path for path in paths if path.is_dir() or path.name.endswith(".py")]
    sh_paths = list(
        itertools.chain.from_iterable(
            (
                path.rglob("*.sh*")
                if path.is_dir()
                else [path] if fnmatch.fnmatch(path.name, "*.sh*") else []
            )
            for path in paths
        )
    )

    shfmt = ["shfmt", "--simplify", "--func-next-line"]

    if not fix:
        if py_paths:
            session.run(
                "mypy",
                "--pretty",
                "--show-error-context",
                "--explicit-package-bases",
                "--",
                *py_paths,
            )
            session.run("pyright", "--warnings", *py_paths)
            session.run("flake8", "--", *py_paths, silent=True)
            session.run("isort", "--check", "--diff", "--", *py_paths)
            session.run("black", "--check", "--diff", "--", *py_paths)

        if sh_paths:
            session.run(
                "shellcheck",
                "--norc",
                "--external-sources",
                "--severity=style",
                "--enable=all",
                "--exclude=" + ",".join(["SC2016", "SC2032", "SC2033", "SC2250", "SC2292"]),
                "--format=gcc",
                "--",
                *sh_paths,
            )
            session.run(*shfmt, "--diff", "--", *sh_paths)

        session.run("reuse", "lint", silent=True)
    else:
        if py_paths:
            session.run("isort", "--", *py_paths)
            session.run("black", "--", *py_paths)

        if sh_paths:
            session.run(*shfmt, "--write", "--", *sh_paths)


def coverage(session: nox.Session) -> None:
    session.install("coverage[toml] >= 7.6.9, < 8")
    session.install("tomli >= 2.2.1, < 3")

    # to measure coverage through a console script, the package has to be installed in editable mode
    session.install("-e", ".")

    nox_session_install_only_end(session)

    for coverage_data_file in pathlib.Path().glob(".coverage*"):
        coverage_data_file.unlink()

    coverage_run = ["no_vtf"]
    env = {
        **session.env,
        "PATH": os.pathsep.join([*(session.bin_paths or []), os.environ.get("PATH") or ""]),
    }
    runner = CoverageTestRunner(coverage_run=coverage_run, paths=session.bin_paths, env=env)
    with TestSuite.with_archived_samples(
        runner=runner, session=session, test_classes=get_test_classes_from_env()
    ) as test_suite:
        test_suite.write()
        test_suite.readback()

    coverage = ["python", "-m", "coverage"]
    session.run(*coverage, "combine", "--quiet", "--append")
    session.run(*coverage, "html")

    if not session.posargs:
        return

    archive_name = str(pathlib.Path(session.invoked_from, session.posargs[0]))
    make_archive(archive_name, base_dir="htmlcov")


if os.name == "posix":
    coverage = nox.session(coverage)


@nox.session
def package(session: nox.Session) -> None:
    session.install("build >= 1.2.2.post1, < 2")

    nox_session_install_only_end(session)

    path_dist = pathlib.Path("dist")
    if path_dist.is_dir():
        dist_files = [path for path in path_dist.iterdir() if path.is_file()]
        for dist_file in dist_files:
            dist_file.unlink()

    session.run("python", "-m", "build", silent=True)

    path_sdist = next(path_dist.glob("*.tar.gz"))
    path_wheel = next(path_dist.glob("*.whl"))

    nox_session_run_pip(session.run, "install", "--force-reinstall", str(path_wheel))

    executable = ["no_vtf"]
    session.run(*executable, "--version")

    runner = TestRunner(cmd=executable, env=session.env, paths=session.bin_paths)
    with TestSuite.with_archived_samples(
        runner=runner, session=session, test_classes=get_test_classes_from_env()
    ) as test_suite:
        test_suite.run([], {})

    if len(session.posargs) >= 1:
        shutil.copy2(path_sdist, pathlib.Path(session.invoked_from, session.posargs[0]))

    if len(session.posargs) >= 2:
        shutil.copy2(path_wheel, pathlib.Path(session.invoked_from, session.posargs[1]))


@nox.session(reuse_venv=False)
def freeze(session: nox.Session) -> None:  # noqa: C901
    build_dir = pathlib.Path("build")
    root_dir = pathlib.Path("dist")
    base_dir = pathlib.Path("no_vtf")
    dst_dir = root_dir / base_dir

    session.install("pyinstaller >= 6.11.1, < 7")

    nox_session_install_only_end(session)

    # installing in editable mode will ensure the _version.py file is generated by setuptools_scm
    # run even with the --no-install flag
    nox_session_run_pip(session.run, "install", "--force-reinstall", "-e", ".")

    if int(os.environ.get("BUILD_NUMPY_FROM_SOURCE", 0)):
        packages = json.loads(
            (
                nox_session_run_pip(
                    session.run,
                    "list",
                    *["--format", "json"],
                    silent=True,
                )
                or "[]"
            )
            .strip()
            .split("\n")[-1]
        )
        numpy = next(package for package in packages if package["name"] == "numpy")

        nox_session_run_pip(
            session.run,
            *["install", "--force-reinstall"],
            *["--no-binary", "numpy"],
            f"numpy == {numpy['version']}",
        )

    tag_cachedir(build_dir)

    session.run("imageio_download_bin", "--package-dir", silent=True)

    pyinstaller_args: list[str] = []

    pyinstaller_args.extend(["--log-level", "WARN"])
    pyinstaller_args.extend(["--name", "no_vtf"])
    pyinstaller_args.extend(["--icon", "resources/pyinstaller/empty.ico"])

    # https://github.com/rsalmei/alive-progress/issues/123
    pyinstaller_args.extend(["--collect-data", "grapheme"])

    # bundle plugin binary dependencies downloaded by imageio_download_bin
    pyinstaller_args.extend(["--collect-binaries", "imageio"])

    pyinstaller_args.append("--noconfirm")
    pyinstaller_args.append("--clean")

    session.run("pyinstaller", *pyinstaller_args, "no_vtf/__main__.py")

    shutil.rmtree(  # pyright: ignore [reportDeprecated]
        dst_dir / "_internal/grapheme/cython", ignore_errors=True
    )

    if os.name == "posix":
        for shared_library in dst_dir.rglob("*.so*"):
            nox_command_run(["strip", "--strip-all", "--", str(shared_library)])

    executable = str(dst_dir / "no_vtf")
    if os.name == "nt":
        executable += ".exe"

    paths = ["."]
    nox_command_run([executable, "--version"], paths=paths, external=True)

    data_subdirs = ["common", os.name]
    data_dirs = [pathlib.Path("resources/pyinstaller") / subdir for subdir in data_subdirs]
    for data_dir in data_dirs:
        if not data_dir.exists():
            continue

        shutil.copytree(data_dir, dst_dir, copy_function=shutil.copy2, dirs_exist_ok=True)

    readme = "README.md"
    shutil.copy2(readme, dst_dir)
    shutil.copy2(f"{readme}.license", dst_dir)

    python_license_dir: pathlib.Path
    if os.name == "nt":
        python_license_dir = pathlib.Path(sys.base_prefix)
    else:
        python_license_dir = pathlib.Path(sysconfig.get_paths("posix_prefix")["stdlib"])

    python_license_file = python_license_dir / "LICENSE.txt"

    licenses_dst_dir = dst_dir / "LICENSES"
    licenses_dst_dir.mkdir(exist_ok=True)

    shutil.copy2(python_license_file, licenses_dst_dir / "LicenseRef-Python.txt")

    if os.name == "nt":
        spdx_license_ids: Sequence[str] = []
        for spdx_license_id in spdx_license_ids:
            shutil.copy2(f"LICENSES/LicenseRef-{spdx_license_id}.txt", licenses_dst_dir)

    nox_session_run_pip(session.run, "install", "--upgrade", "pip")

    nox_session_run_pip(session.run, "install", "pip-licenses >= 5.0.0, < 6")
    nox_session_run_pip(session.run, "install", "pipdeptree >= 2.24.0, < 3")
    nox_session_run_pip(session.run, "install", "reuse >= 5.0.2, < 6")

    dependencies = json.loads(
        session.run(
            "pipdeptree",
            "--warn=fail",
            "--json",
            "--packages",
            ",".join(
                [
                    "no-vtf",
                    "pyinstaller",
                ]
            ),
            silent=True,
        )
        or ""
    )

    session.run(
        "pip-licenses",
        "--from=all",
        "--ignore-packages=pyinstaller-hooks-contrib",
        "--with-authors",
        "--with-urls",
        "--format=plain-vertical",
        f"--output-file={licenses_dst_dir / 'LicenseRef-no-vtf.txt'}",
        "--packages",
        *(dependency["package"]["key"] for dependency in dependencies),
        silent=True,
    )

    lorem_ipsum_path = dst_dir / "_internal/setuptools/_vendor/jaraco/text/Lorem ipsum.txt"
    if lorem_ipsum_path.exists():
        with open(lorem_ipsum_path, "wb"):
            pass

    reuse = [
        "reuse",
        f"--root={dst_dir}",
    ]
    session.run(*reuse, "download", "--all", silent=True)
    session.run(*reuse, "lint", silent=True)

    runner = TestRunner(cmd=[executable], env=session.env, paths=paths, external=True)
    with TestSuite.with_archived_samples(
        runner=runner, session=session, test_classes=get_test_classes_from_env()
    ) as test_suite:
        test_suite.run([], {})

    if not session.posargs:
        return

    if len(session.posargs) >= 2:
        path_sdist = pathlib.Path(session.invoked_from, session.posargs[1])
        shutil.copy2(path_sdist, dst_dir)

    archive_name = str(pathlib.Path(session.invoked_from, session.posargs[0]))
    make_archive(archive_name, root_dir=root_dir, base_dir=base_dir)


@nox.session
def publish(session: nox.Session) -> None:
    session.install("twine >= 6.0.1, < 7")

    nox_session_install_only_end(session)

    if not session.posargs:
        session.error("Path to API token file was not provided")

    dist = pathlib.Path("dist")
    dist_files = [path for path in dist.iterdir() if path.is_file()]
    dist_args = [str(path) for path in dist_files]

    session.run("twine", "check", "--strict", *dist_args)

    upload_args: list[str] = []
    upload_args.append("--non-interactive")
    upload_args.append("--disable-progress-bar")
    upload_args.extend(dist_args)

    env = session.env.copy()
    env["TWINE_USERNAME"] = "__token__"
    env["TWINE_PASSWORD"] = (
        pathlib.Path(session.invoked_from, session.posargs[0]).read_text().strip()
    )

    nox_command_run(
        ["twine", "upload", *upload_args],
        env=env,
        paths=session.bin_paths,
    )


def get_test_classes_from_env() -> Optional[Sequence[str]]:
    run_tests = os.environ.get("RUN_TESTS", "1")
    if not run_tests:
        return []

    try:
        if not int(run_tests):
            return ["InfoTest"]

        return None
    except ValueError:
        return run_tests.split(",")


@nox.session
def test_run(session: nox.Session) -> None:
    session.install("-e", ".")

    nox_session_install_only_end(session)

    opts: dict[str, object] = {
        opt: None for opt in ["always_write", "no_write", "readback", "no_readback"]
    }
    samples: Optional[pathlib.Path] = None
    test_classes: list[str] = []

    for index, arg in enumerate(session.posargs):
        if "--" not in session.posargs[:index] and arg.startswith("-"):
            if not arg.startswith("--"):
                session.error("Short options are not supported")

            if arg != "--":
                opts[arg.removeprefix("--").replace("-", "_")] = ...
        elif not samples:
            samples = pathlib.Path(session.invoked_from, arg)
        else:
            test_classes.append(arg)

    if not samples:
        session.error("Path to test samples was not provided")

    executable = ["no_vtf"]
    runner = TestRunner(cmd=executable, env=session.env, paths=session.bin_paths)
    test_suite = TestSuite(
        test_classes=(test_classes or None), runner=runner, samples=samples, session=session
    )

    test_suite.run([], opts)


@nox.session(reuse_venv=True)
def test_write(session: nox.Session) -> None:
    nox_session_install_only_end(session)

    session.notify("test_run", ["--always-write", "--readback", "--", *session.posargs])


@nox.session(reuse_venv=True)
def test_readback(session: nox.Session) -> None:
    nox_session_install_only_end(session)

    session.notify("test_run", ["--no-write", "--readback", "--", *session.posargs])


def test_update(session: nox.Session) -> None:
    nox_session_install_only_end(session)

    if not session.posargs:
        session.error("Path to new test samples was not provided")

    new_dir = f"{str(pathlib.Path(session.invoked_from, session.posargs[0])).rstrip('/')}/"

    old_dir: Union[pathlib.Path, str]
    with SampleArchives().extract() as old_dir:
        old_dir = f"{str(old_dir).rstrip('/')}/"

        with tempfile.TemporaryDirectory() as diff_dir:
            diff_dir = f"{diff_dir.rstrip('/')}/"

            session.run(
                *[
                    "rsync",
                    "--secluded-args",
                    *(3 * ["--human-readable"]),
                    *["--out-format", "+ %n"],
                    *["--archive", "--no-times"],
                    "--checksum",  # --times caused unnecessary transfers, use the next safest alt.
                    "--prune-empty-dirs",
                    *["--compare-dest", old_dir],
                    "--",
                    *[new_dir, diff_dir],
                ],
                external=True,
            )

            for dirpath, _, filenames in os_walk_strict(old_dir):
                for filename in filenames:
                    old_file = pathlib.Path(dirpath, filename)
                    old_file_relative = old_file.relative_to(old_dir)
                    new_file = pathlib.Path(new_dir, old_file_relative)

                    if not new_file.exists():
                        print(f"- {old_file_relative}")

                        removed_marker_file = pathlib.Path(
                            diff_dir,
                            old_file_relative.parts[0],
                            SampleArchives.REMOVED_SUBDIR,
                            *old_file_relative.parts[1:],
                        )
                        removed_marker_file.parent.mkdir(parents=True, exist_ok=True)
                        removed_marker_file.touch(exist_ok=False)

            session.run(
                *["find", diff_dir],
                *["-maxdepth", "1"],
                *["-type", "f"],
                *["-exec", "rm", "--", "{}", "+"],
                *["-printf", "- %P\\n"],
                external=True,
            )
            session.run(
                *["find", diff_dir],
                *["-type", "d"],
                "-empty",
                "-delete",
                external=True,
            )

            if not pathlib.Path(diff_dir).exists():
                session.skip()

            sample_archives = SampleArchives()
            for path in pathlib.Path(diff_dir).iterdir():
                assert path.is_dir()  # noqa S101 debug check

                new_archive = sample_archives.allocate(
                    path.relative_to(path.parent), ".tar.xz"
                ).resolve(strict=True)

                with session.chdir(path):
                    session.run(
                        "tar",
                        *["--create", "--xz"],
                        *["--file", str(new_archive)],
                        "--",
                        ".",
                        env={"XZ_OPT": "-9"},
                        external=True,
                    )


if os.name == "posix":
    test_update = nox.session(reuse_venv=True)(test_update)


@nox.session(reuse_venv=True)
def test_extract(session: nox.Session) -> None:
    nox_session_install_only_end(session)

    if not session.posargs:
        session.error("Destination path was not provided")
    destination = pathlib.Path(session.invoked_from, session.posargs[0])

    with SampleArchives().extract() as samples:
        shutil.copytree(
            samples, destination, symlinks=True, copy_function=shutil.copy2, dirs_exist_ok=True
        )


def nox_session_is_install_only(session: nox.Session) -> bool:
    logger = nox.logger.logger
    logger_level = logger.level
    try:
        logger.setLevel(logging.WARNING)
        return session.run("python", "--version", silent=True, log=False) is None
    finally:
        logger.setLevel(logger_level)


def nox_session_install_only_end(session: nox.Session) -> None:
    if nox_session_is_install_only(session):
        session.log("Skipping rest of the session, as --install-only is set.")
        session.skip()


class NoxSessionRunner(Protocol):
    def __call__(
        self,
        *args: str | os.PathLike[str],
        env: Mapping[str, str | None] | None = None,
        include_outer_env: bool = True,
        silent: bool = False,
        success_codes: Iterable[int] | None = None,
        log: bool = True,
        external: nox.command.ExternalType | None = None,
        stdout: int | IO[str] | None = None,
        stderr: int | IO[str] | None = subprocess.STDOUT,
        interrupt_timeout: float | None = nox.popen.DEFAULT_INTERRUPT_TIMEOUT,
        terminate_timeout: float | None = nox.popen.DEFAULT_TERMINATE_TIMEOUT,
    ) -> Any | None: ...


def nox_session_get_runner(
    session: nox.Session, *, install_only: bool = False, no_install: bool = True
) -> NoxSessionRunner:
    match nox_session_is_install_only(session), install_only, no_install:
        case _, False, True:
            return session.run
        case _, True, False:
            return session.run_install
        case False, True, True:
            return session.run
        case True, True, True:
            return session.run_install
        case False, False, False:
            return session.run_install
        case True, False, False:
            return session.run

    assert False, "unreachable"  # noqa S101


@overload
def nox_session_run_pip(
    runner: NoxSessionRunner,
    *args: str,
    env: Mapping[str, str] | None = None,
    include_outer_env: bool = True,
    silent: Literal[False],
    success_codes: Iterable[int] | None = None,
    log: bool = True,
    external: Optional[nox.command.ExternalType] = None,
    stdout: int | IO[str] | None = None,
    stderr: int | IO[str] | None = subprocess.STDOUT,
    interrupt_timeout: float | None = nox.popen.DEFAULT_INTERRUPT_TIMEOUT,
    terminate_timeout: float | None = nox.popen.DEFAULT_TERMINATE_TIMEOUT,
) -> Optional[bool]: ...


@overload
def nox_session_run_pip(
    runner: NoxSessionRunner,
    *args: str,
    env: Mapping[str, str] | None = None,
    include_outer_env: bool = True,
    silent: Literal[True],
    success_codes: Iterable[int] | None = None,
    log: bool = True,
    external: Optional[nox.command.ExternalType] = None,
    stdout: int | IO[str] | None = None,
    stderr: int | IO[str] | None = subprocess.STDOUT,
    interrupt_timeout: float | None = nox.popen.DEFAULT_INTERRUPT_TIMEOUT,
    terminate_timeout: float | None = nox.popen.DEFAULT_TERMINATE_TIMEOUT,
) -> Optional[str]: ...


@overload
def nox_session_run_pip(
    runner: NoxSessionRunner,
    *args: str,
    env: Mapping[str, str] | None = None,
    include_outer_env: bool = True,
    silent: bool = False,
    success_codes: Iterable[int] | None = None,
    log: bool = True,
    external: Optional[nox.command.ExternalType] = None,
    stdout: int | IO[str] | None = None,
    stderr: int | IO[str] | None = subprocess.STDOUT,
    interrupt_timeout: float | None = nox.popen.DEFAULT_INTERRUPT_TIMEOUT,
    terminate_timeout: float | None = nox.popen.DEFAULT_TERMINATE_TIMEOUT,
) -> Optional[str | bool]: ...


def nox_session_run_pip(
    runner: NoxSessionRunner,
    *args: str,
    env: Mapping[str, str] | None = None,
    include_outer_env: bool = True,
    silent: bool = False,
    success_codes: Iterable[int] | None = None,
    log: bool = True,
    external: Optional[nox.command.ExternalType] = None,
    stdout: int | IO[str] | None = None,
    stderr: int | IO[str] | None = subprocess.STDOUT,
    interrupt_timeout: float | None = nox.popen.DEFAULT_INTERRUPT_TIMEOUT,
    terminate_timeout: float | None = nox.popen.DEFAULT_TERMINATE_TIMEOUT,
) -> Optional[str | bool]:
    session = getattr(runner, "__self__", None)
    if not isinstance(session, nox.Session):
        raise ValueError(f"runner.__self__: expected nox.Session, got {type(session).__name__}")

    if external is None:
        external = "error" if nox.options.error_on_external_run else False

    env = {
        **(env or {}),
        "PIP_DISABLE_PIP_VERSION_CHECK": "1",
        "PIP_NO_INPUT": "1",
        "PIP_PROGRESS_BAR": "off",
        "PIP_NO_PYTHON_VERSION_WARNING": "1",
    }

    pip = (
        ["uv", "--no-progress", "pip"] if session.venv_backend == "uv" else ["python", "-m", "pip"]
    )

    return runner(
        *pip,
        *args,
        env=env,
        include_outer_env=include_outer_env,
        silent=silent,
        success_codes=success_codes,
        log=log,
        external=external,
        stdout=stdout,
        stderr=stderr,
        interrupt_timeout=interrupt_timeout,
        terminate_timeout=terminate_timeout,
    )


@overload
def nox_command_run(
    args: Sequence[str | os.PathLike[str]],
    *,
    env: Mapping[str, str | None] | None = None,
    silent: Literal[False],
    paths: Sequence[str] | None = None,
    success_codes: Iterable[int] | None = None,
    log: bool = True,
    external: Optional[nox.command.ExternalType] = None,
    stdout: int | IO[str] | None = None,
    stderr: int | IO[str] | None = subprocess.STDOUT,
    interrupt_timeout: float | None = nox.popen.DEFAULT_INTERRUPT_TIMEOUT,
    terminate_timeout: float | None = nox.popen.DEFAULT_TERMINATE_TIMEOUT,
) -> bool: ...


@overload
def nox_command_run(
    args: Sequence[str | os.PathLike[str]],
    *,
    env: Mapping[str, str | None] | None = None,
    silent: Literal[True],
    paths: Sequence[str] | None = None,
    success_codes: Iterable[int] | None = None,
    log: bool = True,
    external: Optional[nox.command.ExternalType] = None,
    stdout: int | IO[str] | None = None,
    stderr: int | IO[str] | None = subprocess.STDOUT,
    interrupt_timeout: float | None = nox.popen.DEFAULT_INTERRUPT_TIMEOUT,
    terminate_timeout: float | None = nox.popen.DEFAULT_TERMINATE_TIMEOUT,
) -> str: ...


@overload
def nox_command_run(
    args: Sequence[str | os.PathLike[str]],
    *,
    env: Mapping[str, str | None] | None = None,
    silent: bool = False,
    paths: Sequence[str] | None = None,
    success_codes: Iterable[int] | None = None,
    log: bool = True,
    external: Optional[nox.command.ExternalType] = None,
    stdout: int | IO[str] | None = None,
    stderr: int | IO[str] | None = subprocess.STDOUT,
    interrupt_timeout: float | None = nox.popen.DEFAULT_INTERRUPT_TIMEOUT,
    terminate_timeout: float | None = nox.popen.DEFAULT_TERMINATE_TIMEOUT,
) -> str | bool: ...


def nox_command_run(
    args: Sequence[str | os.PathLike[str]],
    *,
    env: Mapping[str, str | None] | None = None,
    silent: bool = False,
    paths: Sequence[str] | None = None,
    success_codes: Iterable[int] | None = None,
    log: bool = True,
    external: Optional[nox.command.ExternalType] = None,
    stdout: int | IO[str] | None = None,
    stderr: int | IO[str] | None = subprocess.STDOUT,
    interrupt_timeout: float | None = nox.popen.DEFAULT_INTERRUPT_TIMEOUT,
    terminate_timeout: float | None = nox.popen.DEFAULT_TERMINATE_TIMEOUT,
) -> str | bool:
    if external is None:
        external = "error" if nox.options.error_on_external_run else False
    assert external is not None  # noqa S101 type narrowing

    return nox.command.run(
        args,
        env=env,
        silent=silent,
        paths=paths,
        success_codes=success_codes,
        log=log,
        external=external,
        stdout=stdout,
        stderr=stderr,
        interrupt_timeout=interrupt_timeout,
        terminate_timeout=terminate_timeout,
    )


class _NoxCommandRunKwArgs(TypedDict, total=False):
    stdout: Union[int, IO[str]]
    stderr: Union[int, IO[str]]
    success_codes: Iterable[int]


class _TestRunnerCallKwArgs(TypedDict, total=False):
    additional_env: dict[str, str]


class _RunKwArgs(_NoxCommandRunKwArgs, _TestRunnerCallKwArgs):
    pass


@dataclass(frozen=True, kw_only=True)
class TestRunner:
    cmd: Sequence[str]
    env: Optional[dict[str, str]] = None
    paths: Optional[list[str]] = None
    external: Optional[Union[Literal["error"], bool]] = None

    def __call__(
        self,
        *args: str,
        **kwargs: Unpack[_RunKwArgs],
    ) -> Union[str, bool]:
        full_cmd = list(self.cmd) + list(args)

        env = {**(self.env or os.environ), **kwargs.get("additional_env", {})}

        nox_kwargs = _NoxCommandRunKwArgs()
        if (stdout := kwargs.get("stdout", None)) is not None:
            nox_kwargs["stdout"] = stdout
        if (stderr := kwargs.get("stderr", None)) is not None:
            nox_kwargs["stderr"] = stderr
        if (success_codes := kwargs.get("success_codes", None)) is not None:
            nox_kwargs["success_codes"] = success_codes

        return nox_command_run(
            full_cmd, env=env, paths=self.paths, external=self.external, **nox_kwargs
        )


@dataclass(frozen=True, kw_only=True)
class CoverageTestRunner(TestRunner):
    coverage_run: Sequence[str]

    cmd: Sequence[str] = (
        "timeout",
        "--verbose",
        "--kill-after=10s",
        "5s",
        "python",
        "-m",
        "coverage",
        "run",
    )
    external: Optional[Union[Literal["error"], bool]] = True

    def __call__(
        self,
        *args: str,
        **kwargs: Unpack[_RunKwArgs],
    ) -> Union[str, bool]:
        args = (*self.coverage_run, *args)

        # registering a SIGTERM signal handler may cause the process to hang
        # (https://coverage.readthedocs.io/en/latest/config.html#run-sigterm)
        # this workaround is used to ensure eventual progress in case of hang
        for i in itertools.count(start=1):
            try:
                return super().__call__(*args, **kwargs)
            except nox.command.CommandFailed as exception:
                if exception.reason != "Returned code 124" or i == 10:
                    raise exception

        raise AssertionError("iterating over itertools.count() does not end")


@dataclass(kw_only=True)
class Test:
    runner: TestRunner
    samples: pathlib.Path

    @classmethod
    @contextmanager
    def with_archived_samples(cls, *, runner: TestRunner, **kwargs: object) -> Iterator[Self]:
        with SampleArchives().extract() as samples:
            test = cls(runner=runner, samples=samples, **kwargs)
            yield test

    def write(
        self, args: Optional[Sequence[object]] = None, opts: Optional[dict[str, object]] = None
    ) -> None:
        args = args or []

        opts = opts or {}
        opts = {"always_write": ..., "no_readback": ..., "no_write": None, "readback": None} | opts

        self.run(args, opts)

    def readback(
        self, args: Optional[Sequence[object]] = None, opts: Optional[dict[str, object]] = None
    ) -> None:
        args = args or []

        opts = opts or {}
        opts = {"no_write": ..., "readback": ..., "always_write": None, "no_readback": None} | opts

        self.run(args, opts)

    @final
    def run(self, args: Sequence[object], opts: dict[str, object], /) -> None:
        if not self._pre_run(args, opts):
            return

        exception: Optional[Exception] = None
        try:
            self._run(args, opts)
        except Exception as ex:
            exception = ex

        self._post_run(exception)

    def _pre_run(self, args: Sequence[object], opts: dict[str, object]) -> bool:
        return True

    @abstractmethod
    def _run(self, args: Sequence[object], opts: dict[str, object], /) -> None: ...

    def _post_run(self, exception: Optional[Exception]) -> None:
        if exception:
            raise exception


_TC = TypeVar("_TC", bound="TestCase")
_PS = ParamSpec("_PS")
_TestCaseRun: TypeAlias = Callable[Concatenate[_TC, Sequence[object], dict[str, object], _PS], None]


@dataclass(kw_only=True)
class TestCase(Test):
    def get_samples_subdir(self) -> pathlib.PurePath:
        return pathlib.PurePath(type(self).__name__)

    def get_input_subdir(self) -> pathlib.PurePath:
        return pathlib.PurePath("input")

    def get_output_subdir(self) -> pathlib.PurePath:
        return pathlib.PurePath("output")

    def get_test_samples(self) -> pathlib.Path:
        return self.samples / self.get_samples_subdir()

    def get_input_path(self, subpath: StrPath) -> pathlib.Path:
        return self.get_test_samples() / self.get_input_subdir() / subpath

    def get_output_path(self, subpath: StrPath) -> pathlib.Path:
        return self.get_test_samples() / self.get_output_subdir() / subpath

    @staticmethod
    def and_(
        *decorators: Callable[[_TestCaseRun[_TC, _PS]], _TestCaseRun[_TC, _PS]]
    ) -> Callable[[_TestCaseRun[_TC, _PS]], _TestCaseRun[_TC, _PS]]:
        def decorator(run: _TestCaseRun[_TC, _PS]) -> _TestCaseRun[_TC, _PS]:
            def inner(
                self: _TC,
                args: Sequence[object],
                opts: dict[str, object],
                /,
                *_args: _PS.args,
                **_kwargs: _PS.kwargs,
            ) -> None:
                nonlocal run
                for decorator in decorators:
                    run = decorator(run)

                run(self, args, opts, *_args, **_kwargs)

            return inner

        return decorator

    @staticmethod
    def or_(
        *decorators: Callable[[_TestCaseRun[_TC, _PS]], _TestCaseRun[_TC, _PS]]
    ) -> Callable[[_TestCaseRun[_TC, _PS]], _TestCaseRun[_TC, _PS]]:
        def decorator(run: _TestCaseRun[_TC, _PS]) -> _TestCaseRun[_TC, _PS]:
            def inner(
                self: _TC,
                args: Sequence[object],
                opts: dict[str, object],
                /,
                *_args: _PS.args,
                **_kwargs: _PS.kwargs,
            ) -> None:
                for decorator in decorators:
                    decorator(run)(self, args, opts, *_args, **_kwargs)

            return inner

        return decorator

    @staticmethod
    def with_common_options(
        compress: Optional[bool] = False,
        no_progress: bool = True,
    ) -> Callable[[_TestCaseRun[_TC, _PS]], _TestCaseRun[_TC, _PS]]:
        def decorator(run: _TestCaseRun[_TC, _PS]) -> _TestCaseRun[_TC, _PS]:
            def inner(
                self: _TC,
                args: Sequence[object],
                opts: dict[str, object],
                /,
                *_args: _PS.args,
                **_kwargs: _PS.kwargs,
            ) -> None:
                compress_value = ... if compress is True else None
                no_compress_value = ... if compress is False else None
                no_progress_value = ... if no_progress else None

                opts = {
                    "compress": compress_value,
                    "no_compress": no_compress_value,
                    "no_progress": no_progress_value,
                } | opts
                run(self, args, opts, *_args, **_kwargs)

            return inner

        return decorator

    @staticmethod
    def rw_mode(
        write: Optional[bool] = False,
        readback: bool = False,
    ) -> Callable[[_TestCaseRun[_TC, _PS]], _TestCaseRun[_TC, _PS]]:
        def decorator(run: _TestCaseRun[_TC, _PS]) -> _TestCaseRun[_TC, _PS]:
            def inner(
                self: _TC,
                args: Sequence[object],
                opts: dict[str, object],
                /,
                *_args: _PS.args,
                **_kwargs: _PS.kwargs,
            ) -> None:
                if write is True:
                    opts = {"always_write": ..., "no_write": None} | opts
                elif write is False:
                    opts = {"no_write": ..., "always_write": None} | opts

                if readback:
                    opts = {"readback": ..., "no_readback": None} | opts
                else:
                    opts = {"no_readback": ..., "readback": None} | opts

                run(self, args, opts, *_args, **_kwargs)

            return inner

        return decorator

    @staticmethod
    def with_inputs(
        subpaths: Optional[Sequence[StrPath]] = None,
    ) -> Callable[[_TestCaseRun[_TC, _PS]], _TestCaseRun[_TC, _PS]]:
        def decorator(run: _TestCaseRun[_TC, _PS]) -> _TestCaseRun[_TC, _PS]:
            def inner(
                self: _TC,
                args: Sequence[object],
                opts: dict[str, object],
                /,
                *_args: _PS.args,
                **_kwargs: _PS.kwargs,
            ) -> None:
                nonlocal subpaths
                subpaths = subpaths or [pathlib.PurePath()]
                input_paths = [self.get_input_path(subpath) for subpath in subpaths]

                args = input_paths + list(args)
                run(self, args, opts, *_args, **_kwargs)

            return inner

        return decorator

    @staticmethod
    def in_place() -> Callable[[_TestCaseRun[_TC, _PS]], _TestCaseRun[_TC, _PS]]:
        def decorator(run: _TestCaseRun[_TC, _PS]) -> _TestCaseRun[_TC, _PS]:
            def inner(
                self: _TC,
                args: Sequence[object],
                opts: dict[str, object],
                /,
                *_args: _PS.args,
                **_kwargs: _PS.kwargs,
            ) -> None:
                opts = {"output_dir": None, "output_file": None} | opts
                run(self, args, opts, *_args, **_kwargs)

            return inner

        return decorator

    @staticmethod
    def to_directory(
        subpath: Optional[StrPath] = None,
    ) -> Callable[[_TestCaseRun[_TC, _PS]], _TestCaseRun[_TC, _PS]]:
        def decorator(run: _TestCaseRun[_TC, _PS]) -> _TestCaseRun[_TC, _PS]:
            def inner(
                self: _TC,
                args: Sequence[object],
                opts: dict[str, object],
                /,
                *_args: _PS.args,
                **_kwargs: _PS.kwargs,
            ) -> None:
                nonlocal subpath
                subpath = subpath or pathlib.PurePath()
                output_path = self.get_output_path(subpath)

                opts = {"output_dir": output_path, "output_file": None} | opts
                run(self, args, opts, *_args, **_kwargs)

            return inner

        return decorator

    @staticmethod
    def to_file(
        subpath: StrPath,
    ) -> Callable[[_TestCaseRun[_TC, _PS]], _TestCaseRun[_TC, _PS]]:
        def decorator(run: _TestCaseRun[_TC, _PS]) -> _TestCaseRun[_TC, _PS]:
            def inner(
                self: _TC,
                args: Sequence[object],
                opts: dict[str, object],
                /,
                *_args: _PS.args,
                **_kwargs: _PS.kwargs,
            ) -> None:
                output_path = self.get_output_path(subpath)

                opts = {"output_file": output_path, "output_dir": None} | opts
                run(self, args, opts, *_args, **_kwargs)

            return inner

        return decorator

    @staticmethod
    def parametrize(
        *opt_sets: dict[str, object]
    ) -> Callable[[_TestCaseRun[_TC, _PS]], _TestCaseRun[_TC, _PS]]:
        def decorator(run: _TestCaseRun[_TC, _PS]) -> _TestCaseRun[_TC, _PS]:
            def inner(
                self: _TC,
                args: Sequence[object],
                opts: dict[str, object],
                /,
                *_args: _PS.args,
                **_kwargs: _PS.kwargs,
            ) -> None:
                for opt_set in opt_sets:
                    parametrized_opts = {**opt_set} | opts
                    run(self, args, parametrized_opts, *_args, **_kwargs)

            return inner

        return decorator

    @staticmethod
    def test_filter(  # noqa: C901
        option: str,
        subpath: StrPath,
        num_items: int,
        *,
        animate: Optional[bool] = None,
        ldr_format: Optional[str] = None,
        hdr_format: Optional[str] = "skip",
    ) -> Callable[[_TestCaseRun[_TC, _PS]], _TestCaseRun[_TC, _PS]]:
        def decorator(run: _TestCaseRun[_TC, _PS]) -> _TestCaseRun[_TC, _PS]:
            def inner(
                self: _TC,
                args: Sequence[object],
                opts: dict[str, object],
                /,
                *_args: _PS.args,
                **_kwargs: _PS.kwargs,
            ) -> None:
                input_file = self.get_input_path(subpath)
                args = [input_file] + list(args)

                nonlocal ldr_format
                ldr_format = ldr_format or ("apng" if animate else "tiff")
                opts = {"ldr_format": ldr_format} | opts

                if hdr_format:
                    opts = {"hdr_format": hdr_format} | opts

                if animate is True:
                    opts = {"animate": ...} | opts
                elif animate is False:
                    opts = {"no_animate": ...} | opts

                indices_pos = [1, num_items - 1]
                indices_neg = [-index for index in indices_pos]
                indices = [None] + indices_pos + indices_neg
                steps = [None, -2]

                def iter_run(filter_str: str) -> None:
                    iter_opts = {option: filter_str} | opts

                    iter_subpath = pathlib.Path(subpath)
                    filter_path = filter_str.replace(":", ",")
                    output_stem = f"{iter_subpath.stem}_{filter_path}"

                    if animate:
                        output_subpath = iter_subpath.with_name(f"{output_stem}.{ldr_format}")
                        output_file = self.get_output_path(output_subpath)

                        iter_opts = {"output_file": output_file} | iter_opts
                    else:
                        output_dir = self.get_output_path(output_stem)
                        output_dir.mkdir(parents=True, exist_ok=True)

                        iter_opts = {"output_dir": output_dir} | iter_opts

                    run(self, args, iter_opts, *_args, **_kwargs)

                for index in indices:
                    index = index or 0
                    if index < -num_items or index >= num_items:
                        continue

                    iter_run(str(index))

                for start, stop, step in itertools.product(indices, indices, steps):
                    if not len(range(num_items)[slice(start, stop, step)]):
                        continue

                    def str_optional(o: Optional[object], /) -> str:
                        return str(o) if o is not None else ""

                    filter_str = ""
                    filter_str += f"{str_optional(start)}:{str_optional(stop)}"
                    if step is not None:
                        filter_str += f":{str_optional(step)}"

                    iter_run(filter_str)

            return inner

        return decorator

    @with_common_options()
    def _run(
        self, args: Sequence[object], opts: dict[str, object], /, **_kwargs: Unpack[_RunKwArgs]
    ) -> None:
        if opts.get("compress") and opts.get("no_compress"):
            raise ValueError("compress and no_compress are exclusive")

        if opts.get("always_write") and opts.get("no_write"):
            raise ValueError("always_write and no_write are exclusive")

        if opts.get("readback") and opts.get("no_readback"):
            raise ValueError("readback and no_readback are exclusive")

        parameters = self._str_opts(opts) + self._str_args(args)
        self.runner(*parameters, **_kwargs)

    def _str_opts(self, opts: dict[str, object]) -> list[str]:
        str_opts: list[str] = []
        for name, value in opts.items():
            if value is None:
                continue

            str_opt = "--" + name.replace("_", "-")
            str_opts.append(str_opt)

            if value is not Ellipsis:
                value = str(value)
                str_opts.append(value)

        return str_opts

    def _str_args(self, args: Sequence[object]) -> list[str]:
        if not args:
            return []

        str_args = ["--"]
        str_args.extend(str(arg) for arg in args)
        return str_args


@dataclass(kw_only=True)
class TestSuite(Test):
    test_classes: Optional[Sequence[Union[type[TestCase], str]]] = None

    session: Optional[nox.Session] = None

    @overload
    @classmethod
    def register(
        cls, test_class: type[_TC], /, *, condition: Optional[bool] = None
    ) -> type[_TC]: ...

    @overload
    @classmethod
    def register(
        cls, /, *, condition: Optional[bool] = None
    ) -> Callable[[type[_TC]], type[_TC]]: ...

    @classmethod
    def register(
        cls, test_class: Optional[type[_TC]] = None, /, *, condition: Optional[bool] = None
    ) -> Union[type[_TC], Callable[[type[_TC]], type[_TC]]]:
        if not test_class:
            return functools.partial(cls.register, condition=condition)

        if condition is not False:
            cls._registered_test_classes[test_class.__name__] = test_class

        return test_class

    _registered_test_classes: ClassVar[dict[str, type[TestCase]]] = {}

    def __post_init__(self) -> None:
        self._test_instances: list[TestCase] = []

        test_classes = self.test_classes or self._registered_test_classes.values()
        for test_class in test_classes:
            if isinstance(test_class, str):
                test_class = self._registered_test_classes[test_class]

            test_instance = test_class(runner=self.runner, samples=self.samples)
            self._test_instances.append(test_instance)

    def _run(self, args: Sequence[object], opts: dict[str, object], /) -> None:
        for test_instance in self._test_instances:
            if self.session:
                self.session.log(f"Running {type(test_instance).__name__}: {args = } {opts = }")

            test_instance.run(args, opts)


@TestSuite.register
@dataclass(kw_only=True)
class InfoTest(TestCase):
    @TestCase.or_(
        TestCase.parametrize({"help": ...}),  # pyright: ignore [reportArgumentType]
        TestCase.parametrize({"version": ...}),
        TestCase.parametrize({"credits": ...}),
    )
    def _run(
        self, args: Sequence[object], opts: dict[str, object], /, **_kwargs: Unpack[_RunKwArgs]
    ) -> None:
        super()._run(args, opts, **_kwargs)


@TestSuite.register
@dataclass(kw_only=True)
class WriteSelfTest(TestCase):
    def get_samples_subdir(self) -> pathlib.PurePath:
        return pathlib.PurePath("FormatTest")

    def get_output_subdir(self) -> pathlib.PurePath:
        return pathlib.PurePath("write_self_test_output")

    def _pre_run(self, args: Sequence[object], opts: dict[str, object]) -> bool:
        if "no_write" in opts and opts["no_write"] is not None:
            return False

        output_path = self.get_output_path("")
        shutil.rmtree(output_path, ignore_errors=True)  # pyright: ignore [reportDeprecated]
        output_path.mkdir()

        return True

    @TestCase.rw_mode(write=None)
    @TestCase.with_inputs()
    @TestCase.to_directory()
    def _run(
        self, args: Sequence[object], opts: dict[str, object], /, **_kwargs: Unpack[_RunKwArgs]
    ) -> None:
        super()._run(args, opts, **_kwargs)

    def _post_run(self, exception: Optional[Exception]) -> None:
        super()._post_run(exception)

        input_path = self.get_input_path("")
        output_path = self.get_output_path("")

        num_output_files_expected = 0
        for path in input_path.iterdir():
            if not path.is_file():
                continue

            stem_re = re.escape(path.stem)
            extension_re = r"\.[^\./]+$"

            envmap_6_faces_re = r"(?:bk|dn|ft|lf|rt|up)"
            envmap_7_faces_re = r"(?:" + envmap_6_faces_re + "|sph)"
            match path.stem:
                case "envmap_6_faces":
                    additional_re = envmap_6_faces_re
                case "envmap_7_faces":
                    additional_re = envmap_7_faces_re
                case _:
                    additional_re = r""

            pattern = re.compile(stem_re + additional_re + extension_re, re.ASCII)

            output_files = list(path_re_glob(output_path, pattern))
            num_output_files_expected += len(output_files)

        num_output_files_actual = len([path for path in output_path.iterdir() if path.is_file()])
        if num_output_files_actual != num_output_files_expected:
            raise ValueError("Number of expected and actual written files must match")

        shutil.rmtree(output_path)  # pyright: ignore [reportDeprecated]


@TestSuite.register
@dataclass(kw_only=True)
class ReadbackNegativeSelfTest(TestCase):
    def get_input_path(self, subpath: StrPath) -> pathlib.Path:
        return self.samples / subpath

    def get_output_path(self, subpath: StrPath) -> pathlib.Path:
        return self.samples / subpath

    def _pre_run(self, args: Sequence[object], opts: dict[str, object]) -> bool:
        return not any(
            (
                ("no_write" in opts and opts["no_write"] is None),
                ("readback" in opts and opts["readback"] is None),
                ("always_write" in opts and opts["always_write"] is not None),
                ("no_readback" in opts and opts["no_readback"] is not None),
            )
        )

    @TestCase.rw_mode(readback=True)
    @TestCase.or_(
        TestCase.and_(  # pyright: ignore [reportArgumentType]
            TestCase.with_inputs(["FormatTest/input/rgb888.vtf"]),
            TestCase.to_directory("FormatTest/nonexistent_directory"),
        ),
        TestCase.and_(
            TestCase.with_inputs(["FormatTest/input/rgb888.vtf"]),
            TestCase.to_file("FormatTest/output/nonexistent_file.tiff"),
        ),
        TestCase.and_(
            TestCase.with_inputs(["FormatTest/input/rgb888.vtf"]),
            TestCase.to_file("FormatTest/output/rgba8888.tiff"),
        ),
        TestCase.and_(
            TestCase.with_inputs(["FormatTest/input/bgra8888.vtf"]),
            TestCase.to_file("FormatTest/output/bgra8888_hdr.tiff"),
        ),
        TestCase.and_(
            TestCase.with_inputs(["MultipleFramesTest/input/8x8_.vtf"]),
            TestCase.to_file("MultipleFramesTest/output/8x8__,-1.apng"),
            TestCase.parametrize({"animate": ..., "ldr_format": "apng"}),
        ),
        TestCase.and_(
            TestCase.with_inputs(["FormatTest/input/rgb888.vtf"]),
            TestCase.to_file("FormatTest/output/rgba8888.raw"),
            TestCase.parametrize({"raw": ...}),
        ),
        TestCase.and_(
            TestCase.with_inputs(["FormatTest/input/i8.vtf"]),
            TestCase.to_file("FormatTest/output/i8_extra_null_byte.raw"),
            TestCase.parametrize({"raw": ...}),
        ),
    )
    def _run(
        self, args: Sequence[object], opts: dict[str, object], /, **_kwargs: Unpack[_RunKwArgs]
    ) -> None:
        _kwargs = {"success_codes": [1, 2], **_kwargs}
        super()._run(args, opts, **_kwargs)


@TestSuite.register
@dataclass(kw_only=True)
class FormatTest(TestCase):
    @TestCase.rw_mode(readback=True)
    @TestCase.with_inputs()
    @TestCase.to_directory()
    @TestCase.parametrize({}, {"mipmaps": ...})
    @TestCase.parametrize({}, {"separate_channels": ...})
    def _run(
        self, args: Sequence[object], opts: dict[str, object], /, **_kwargs: Unpack[_RunKwArgs]
    ) -> None:
        ldr_formats = ["png", "tga", "tiff", "apng"]
        for ldr_format in ldr_formats:
            super()._run(args, {"ldr_format": ldr_format, "hdr_format": "skip"} | opts, **_kwargs)

        hdr_formats = ["exr", "tiff"]
        for hdr_format in hdr_formats:
            super()._run(args, {"ldr_format": "skip", "hdr_format": hdr_format} | opts, **_kwargs)

        super()._run(args, {"raw": ...} | opts, **_kwargs)


@TestSuite.register
@dataclass(kw_only=True)
class MultipleFramesTest(TestCase):
    @TestCase.rw_mode(readback=True)
    @TestCase.or_(
        TestCase.and_(  # pyright: ignore [reportArgumentType]
            TestCase.with_inputs(["8x8_.vtf"]),
            TestCase.to_directory(),
            TestCase.parametrize({"no_animate": ...}),
            TestCase.parametrize({}, {"mipmaps": ...}),
            TestCase.parametrize({}, {"separate_channels": ...}),
        ),
        TestCase.test_filter("frames", "8x8_.vtf", 64, animate=False),
        TestCase.test_filter("frames", "8x8_.vtf", 64, animate=True),
    )
    def _run(
        self, args: Sequence[object], opts: dict[str, object], /, **_kwargs: Unpack[_RunKwArgs]
    ) -> None:
        super()._run(args, opts, **_kwargs)


@TestSuite.register
@dataclass(kw_only=True)
class MultipleSlicesTest(TestCase):
    @TestCase.rw_mode(readback=True)
    @TestCase.or_(
        TestCase.and_(  # pyright: ignore [reportArgumentType]
            TestCase.with_inputs(["volume.vtf"]),
            TestCase.to_directory(),
            TestCase.parametrize({}, {"mipmaps": ...}),
            TestCase.parametrize({}, {"separate_channels": ...}),
        ),
        TestCase.test_filter("slices", "volume.vtf", 256),
    )
    def _run(
        self, args: Sequence[object], opts: dict[str, object], /, **_kwargs: Unpack[_RunKwArgs]
    ) -> None:
        super()._run(args, opts, **_kwargs)


@TestSuite.register
@dataclass(kw_only=True)
class MultipleFacesTest(TestCase):
    @TestCase.rw_mode(readback=True)
    @TestCase.test_filter("faces", "envmap_7_faces.vtf", 7)
    def _run(
        self, args: Sequence[object], opts: dict[str, object], /, **_kwargs: Unpack[_RunKwArgs]
    ) -> None:
        super()._run(args, opts, **_kwargs)


@TestSuite.register
@dataclass(kw_only=True)
class VersionTest(TestCase):
    @TestCase.rw_mode(readback=True)
    @TestCase.or_(
        TestCase.with_inputs(["rgb888_v7.0.vtf"]),  # pyright: ignore [reportArgumentType]
        TestCase.with_inputs(["rgb888_v7.1.vtf"]),
        TestCase.with_inputs(["rgb888_v7.2.vtf"]),
        TestCase.with_inputs(["rgb888_v7.3.vtf"]),
        TestCase.with_inputs(["rgb888_v7.4.vtf"]),
        TestCase.with_inputs(["rgb888_v7.5.vtf"]),
    )
    @TestCase.to_directory()
    @TestCase.parametrize({}, {"mipmaps": ...})
    def _run(
        self, args: Sequence[object], opts: dict[str, object], /, **_kwargs: Unpack[_RunKwArgs]
    ) -> None:
        super()._run(args, opts, **_kwargs)


@TestSuite.register
@dataclass(kw_only=True)
class LowResolutionImageTest(TestCase):
    def get_samples_subdir(self) -> pathlib.PurePath:
        return pathlib.PurePath("VersionTest")

    @TestCase.rw_mode(readback=True)
    @TestCase.or_(
        TestCase.with_inputs(["rgb888_v7.0.vtf"]),  # pyright: ignore [reportArgumentType]
        TestCase.with_inputs(["rgb888_v7.1.vtf"]),
        TestCase.with_inputs(["rgb888_v7.2.vtf"]),
        TestCase.with_inputs(["rgb888_v7.3.vtf"]),
        TestCase.with_inputs(["rgb888_v7.4.vtf"]),
        TestCase.with_inputs(["rgb888_v7.5.vtf"]),
    )
    @TestCase.to_directory("low_res_img")
    @TestCase.parametrize({"low_res_img": ...})
    def _run(
        self, args: Sequence[object], opts: dict[str, object], /, **_kwargs: Unpack[_RunKwArgs]
    ) -> None:
        super()._run(args, opts, **_kwargs)


@TestSuite.register
@dataclass(kw_only=True)
class PathTest(TestCase):
    def get_input_subdir(self) -> pathlib.PurePath:
        return pathlib.PurePath()

    @TestCase.rw_mode(readback=True)
    @TestCase.or_(
        TestCase.and_(  # pyright: ignore [reportArgumentType]
            TestCase.with_inputs(
                [
                    "input/a.vtf/b/c.vtf",
                    "input/a.vtf",
                    "input/a.vtf/b",
                    "input",
                    "input/a.vtf/b/c.vtf",
                ]
            ),
            TestCase.to_directory("to_directory"),
        ),
        TestCase.and_(
            TestCase.with_inputs(["input/a.vtf/b/c.vtf"]),
            TestCase.to_file("to_file/c.tiff"),
        ),
        TestCase.and_(
            TestCase.with_inputs(["in_place"]),
            TestCase.in_place(),
        ),
    )
    @TestCase.parametrize({"ldr_format": "png", "hdr_format": "skip"})
    def _run(
        self, args: Sequence[object], opts: dict[str, object], /, **_kwargs: Unpack[_RunKwArgs]
    ) -> None:
        super()._run(args, opts, **_kwargs)


@TestSuite.register
@dataclass(kw_only=True)
class UnsupportedFormatTest(TestCase):
    def get_samples_subdir(self) -> pathlib.PurePath:
        return pathlib.PurePath("FormatTest")

    @TestCase.rw_mode(readback=True)
    @TestCase.with_inputs()
    @TestCase.to_directory()
    @TestCase.parametrize({"ldr_format": "ppm", "hdr_format": "skip", "separate_channels": ...})
    def _run(
        self, args: Sequence[object], opts: dict[str, object], /, **_kwargs: Unpack[_RunKwArgs]
    ) -> None:
        super()._run(args, opts, **_kwargs)


@TestSuite.register
@dataclass(kw_only=True)
class SequentialRunnerTest(TestCase):
    def get_samples_subdir(self) -> pathlib.PurePath:
        return pathlib.PurePath("FormatTest")

    @TestCase.rw_mode(readback=True)
    @TestCase.with_inputs()
    @TestCase.to_directory()
    @TestCase.parametrize({"num_workers": 1})
    def _run(
        self, args: Sequence[object], opts: dict[str, object], /, **_kwargs: Unpack[_RunKwArgs]
    ) -> None:
        super()._run(args, opts, **_kwargs)


@TestSuite.register
@dataclass(kw_only=True)
class ResolutionFilterTest(TestCase):
    def get_samples_subdir(self) -> pathlib.PurePath:
        return pathlib.PurePath("FormatTest")

    @TestCase.rw_mode(readback=True)
    @TestCase.with_inputs(["rgb888.vtf"])
    @TestCase.or_(
        TestCase.and_(  # pyright: ignore [reportArgumentType]
            TestCase.to_file("rgb888_min_512px.tiff"),
            TestCase.parametrize({"min_resolution": 512}),
        ),
        TestCase.and_(
            TestCase.to_file("rgb888_min_2048px_closest.tiff"),
            TestCase.parametrize({"min_resolution": 2048, "closest_resolution": ...}),
        ),
        TestCase.and_(
            TestCase.to_file("rgb888_max_256px.tiff"),
            TestCase.parametrize({"max_resolution": 256}),
        ),
    )
    def _run(
        self, args: Sequence[object], opts: dict[str, object], /, **_kwargs: Unpack[_RunKwArgs]
    ) -> None:
        super()._run(args, opts, **_kwargs)


@TestSuite.register
@dataclass(kw_only=True)
class ProgressBarTest(TestCase):
    def get_samples_subdir(self) -> pathlib.PurePath:
        return pathlib.PurePath("FormatTest")

    @TestCase.rw_mode(readback=True)
    @TestCase.with_inputs()
    @TestCase.to_directory()
    @TestCase.with_common_options(no_progress=False)
    def _run(
        self, args: Sequence[object], opts: dict[str, object], /, **_kwargs: Unpack[_RunKwArgs]
    ) -> None:
        super()._run(args, opts, **_kwargs)


@TestSuite.register
@dataclass(kw_only=True)
class HdrToLdrTest(TestCase):
    def get_samples_subdir(self) -> pathlib.PurePath:
        return pathlib.PurePath("FormatTest")

    @TestCase.rw_mode(readback=True)
    @TestCase.or_(
        TestCase.and_(  # pyright: ignore [reportArgumentType]
            TestCase.with_inputs(
                [
                    "bgra8888_hdr.vtf",
                    "rgb0-rgba16161616f_hdr.vtf",
                    "rgba16161616f_hdr.vtf",
                    "rgba16161616_hdr.vtf",
                ]
            ),
            TestCase.to_directory("hdr_to_ldr"),
        ),
        TestCase.and_(
            TestCase.with_inputs(["bgra8888.vtf"]),
            TestCase.to_directory(),
        ),
    )
    @TestCase.parametrize({"hdr_to_ldr": ...})
    def _run(
        self, args: Sequence[object], opts: dict[str, object], /, **_kwargs: Unpack[_RunKwArgs]
    ) -> None:
        super()._run(args, opts, **_kwargs)


@TestSuite.register
@dataclass(kw_only=True)
class RawIsUnaffectedByOtherFlagsTest(TestCase):
    def get_samples_subdir(self) -> pathlib.PurePath:
        return pathlib.PurePath("FormatTest")

    @TestCase.rw_mode(readback=True)
    @TestCase.with_inputs()
    @TestCase.to_directory()
    @TestCase.parametrize({"raw": ...})
    @TestCase.parametrize({"hdr_to_ldr": ..., "separate_channels": ...})
    def _run(
        self, args: Sequence[object], opts: dict[str, object], /, **_kwargs: Unpack[_RunKwArgs]
    ) -> None:
        super()._run(args, opts, **_kwargs)


@TestSuite.register
@dataclass(kw_only=True)
class PipelineStepsTest(TestCase):
    @TestCase.rw_mode(readback=True)
    @TestCase.with_inputs()
    @TestCase.to_directory()
    @TestCase.parametrize({"no_animate": ...}, {"ldr_format": "apng"})
    @TestCase.or_(
        TestCase.parametrize({}, {"raw": ...}),  # pyright: ignore [reportArgumentType]
        TestCase.and_(
            TestCase.parametrize({}, {"hdr_to_ldr": ...}),
            TestCase.parametrize({}, {"separate_channels": ...}),
        ),
    )
    def _run(
        self, args: Sequence[object], opts: dict[str, object], /, **_kwargs: Unpack[_RunKwArgs]
    ) -> None:
        super()._run(args, opts, **_kwargs)


@TestSuite.register
@dataclass(kw_only=True)
class DynamicRangeOverrideTest(TestCase):
    def get_samples_subdir(self) -> pathlib.PurePath:
        return pathlib.PurePath("FormatTest")

    @TestCase.rw_mode(readback=True)
    @TestCase.or_(
        TestCase.and_(  # pyright: ignore [reportArgumentType]
            TestCase.with_inputs(["bgra8888.vtf"]),
            TestCase.to_file("bgra8888_hdr.exr"),
            TestCase.parametrize({"dynamic_range": "hdr"}),
        ),
        TestCase.and_(
            TestCase.with_inputs(["bgra8888_hdr.vtf"]),
            TestCase.to_file("bgra8888.tiff"),
            TestCase.parametrize({"dynamic_range": "ldr"}),
        ),
    )
    def _run(
        self, args: Sequence[object], opts: dict[str, object], /, **_kwargs: Unpack[_RunKwArgs]
    ) -> None:
        super()._run(args, opts, **_kwargs)


@TestSuite.register
@dataclass(kw_only=True)
class OverbrightFactorTest(TestCase):
    def get_samples_subdir(self) -> pathlib.PurePath:
        return pathlib.PurePath("FormatTest")

    @TestCase.rw_mode(readback=True)
    @TestCase.with_inputs(["bgra8888_hdr.vtf"])
    @TestCase.to_file("bgra8888_hdr_overbright_factor_8.exr")
    @TestCase.parametrize({"overbright_factor": 8})
    def _run(
        self, args: Sequence[object], opts: dict[str, object], /, **_kwargs: Unpack[_RunKwArgs]
    ) -> None:
        super()._run(args, opts, **_kwargs)


@TestSuite.register
@dataclass(kw_only=True)
class CommaSeparatedFramesFilterTest(TestCase):
    def get_samples_subdir(self) -> pathlib.PurePath:
        return pathlib.PurePath("MultipleFramesTest")

    @TestCase.rw_mode(readback=True)
    @TestCase.with_inputs(["8x8_.vtf"])
    @TestCase.to_file("8x8__,,9;-2,-8,-1;-8,1,-8.apng")
    @TestCase.parametrize({"frames": "::9,-2:-8:-1,-8:1:-8"})
    def _run(
        self, args: Sequence[object], opts: dict[str, object], /, **_kwargs: Unpack[_RunKwArgs]
    ) -> None:
        super()._run(args, opts, **_kwargs)


if sys.platform == "linux":  # noqa: C901
    _OutputStream: TypeAlias = Optional[pathlib.Path]
    _OutputStreams: TypeAlias = tuple[_OutputStream, _OutputStream]

    @TestSuite.register
    @dataclass(kw_only=True)
    class ShellCompletionTest(TestCase):
        @TestCase.rw_mode(readback=True)
        @TestCase.with_common_options(compress=None, no_progress=False)
        def _run(
            self, args: Sequence[object], opts: dict[str, object], /, **_kwargs: Unpack[_RunKwArgs]
        ) -> None:
            if opts.get("always_write") and opts.get("no_write"):
                raise ValueError("always_write and no_write are exclusive")

            if opts.get("readback") and opts.get("no_readback"):
                raise ValueError("readback and no_readback are exclusive")

            write = opts.pop("always_write", None) is not None
            readback = opts.pop("readback", None) is not None
            opts.pop("no_write", None)
            opts.pop("no_readback", None)

            unsupported_shell = "unsupported"

            def run(shell: str, actual: _OutputStreams, expected: _OutputStreams) -> None:
                stdout, stderr = actual

                opener = functools.partial(mkdir_parents_opener, mode=0o666)
                open_output = functools.partial(open, mode="wb", opener=opener)
                open_pty = contextmanager_bind(
                    dummy_pty(), functools.partial(os.fdopen, mode="wb", closefd=False)
                )
                with optional_contexts(
                    open_output(stdout) if stdout else open_pty,
                    open_output(stderr) if stderr else None,
                ) as (stdout_file, stderr_file):
                    run_kwargs = _RunKwArgs(
                        additional_env={"_CONSOLE_SCRIPT_PATH_OVERRIDE": "/test/path/no_vtf"}
                    )

                    if stdout_file:
                        run_kwargs["stdout"] = stdout_file.fileno()

                    if stderr_file:
                        run_kwargs["stderr"] = stderr_file.fileno()

                    if stdout and shell == unsupported_shell:
                        run_kwargs["success_codes"] = [1]

                    run_kwargs.update(_kwargs)

                    super(ShellCompletionTest, self)._run(
                        args, {"shell_completion": shell} | opts, **run_kwargs
                    )

                for actual_stream, expected_stream in zip(actual, expected, strict=True):
                    if not (actual_stream and expected_stream):
                        continue

                    nox_command_run(
                        [
                            *["git", "--no-pager", "--literal-pathspecs"],
                            *["diff", "--no-index", "--exit-code", "--unified", "--histogram"],
                            *["--src-prefix", "expected/"],
                            *["--dst-prefix", "actual/"],
                            "--",
                            *[str(expected_stream), str(actual_stream)],
                        ],
                        env={
                            **os.environ,
                            "GIT_CONFIG_GLOBAL": "/dev/null",
                            "GIT_CONFIG_SYSTEM": "/dev/null",
                        },
                    )

            for shell, redirect_stdout in itertools.product(
                [unsupported_shell, "bash", "zsh", "fish"], [False, True]
            ):
                test_step_path = (
                    self.get_test_samples()
                    / shell
                    / ("stdout_file" if redirect_stdout else "stdout_tty")
                )
                expected_stdout: Optional[pathlib.Path] = test_step_path / "stdout"
                expected_stderr: Optional[pathlib.Path] = test_step_path / "stderr"

                with optional_contexts(
                    (expected_stdout if write else tempfile_name()) if redirect_stdout else None,
                    expected_stderr if write else tempfile_name(),
                    expected_stdout if readback and redirect_stdout else None,
                    expected_stderr if readback else None,
                ) as (actual_stdout, actual_stderr, expected_stdout, expected_stderr):
                    run(shell, (actual_stdout, actual_stderr), (expected_stdout, expected_stderr))


if sys.platform == "linux":

    @contextmanager
    def dummy_pty() -> Iterator[int]:
        def copy() -> None:
            with contextlib.suppress(OSError):
                while os.read(master_fd, 16 * 1024):
                    pass

        thread = threading.Thread(target=copy, daemon=True)

        master_fd, slave_fd = pty.openpty()
        try:
            fcntl.ioctl(slave_fd, termios.TIOCEXCL)
            tty.setraw(master_fd, termios.TCSANOW)

            thread.start()

            yield slave_fd
        finally:
            os.close(slave_fd)

            if thread.ident:
                thread.join()

            os.close(master_fd)


@contextmanager
def tempfile_name() -> Iterator[pathlib.Path]:
    with tempfile.NamedTemporaryFile() as named_tempfile:
        yield pathlib.Path(named_tempfile.name)


class SampleArchives:
    REMOVED_SUBDIR: Final = pathlib.PurePath("._removed")

    def __init__(self, top: Optional[pathlib.Path] = None) -> None:
        self.top: Final = top or pathlib.Path("resources/test/samples")

    def subdirs(self) -> Iterator[pathlib.PurePath]:
        for path in self.top.iterdir():
            if path.is_dir():
                yield path.relative_to(self.top)

    def archives(self, subdir: pathlib.PurePath) -> Sequence[pathlib.Path]:
        archives_dir = self._get_archives_dir(subdir)
        if not archives_dir.exists():
            return []

        return sorted(
            (
                path
                for path in archives_dir.iterdir()
                if not (path.is_dir() or path.name.endswith(".license"))
            ),
            key=lambda path: (len(path.name), path),
        )

    def allocate(self, subdir: pathlib.PurePath, extension: str) -> pathlib.Path:
        new_archive_stem = "1"
        if archives := self.archives(subdir):
            new_archive_stem = str(int(archives[-1].name.split(".")[0]) + 1)

        new_archive = (self._get_archives_dir(subdir) / new_archive_stem).with_suffix(extension)

        new_archive.parent.mkdir(parents=True, exist_ok=True)
        new_archive.touch(exist_ok=False)

        return new_archive

    @contextmanager
    def extract(self) -> Iterator[pathlib.Path]:
        with tempfile.TemporaryDirectory() as output_name:
            output_directory = pathlib.Path(output_name)

            for subdir in self.subdirs():
                extract_dir = output_directory / subdir
                extract_dir.mkdir(parents=True, exist_ok=True)

                for archive in self.archives(subdir):
                    shutil.unpack_archive(archive, extract_dir)

                    removed_dir = extract_dir / self.REMOVED_SUBDIR
                    if removed_dir.exists():
                        for dirpath, _, filenames in os_walk_strict(removed_dir):
                            for filename in filenames:
                                removed_marker = pathlib.Path(dirpath, filename)
                                removed_marker_relative = removed_marker.relative_to(removed_dir)

                                (extract_dir / removed_marker_relative).unlink(missing_ok=True)
                                (removed_dir / removed_marker_relative).unlink(missing_ok=False)

            for dirpath, dirnames, filenames in os_walk_strict(output_directory, topdown=False):
                # update dirnames: the list of subdirectories is retrieved before the tuples for the
                # directory and its subdirectories are generated; and the directories in dirnames
                # have already been generated by the time dirnames itself is generated
                dirnames = [
                    dirname for dirname in dirnames if pathlib.Path(dirpath, dirname).exists()
                ]

                if not (dirnames or filenames):
                    pathlib.Path(dirpath).rmdir()

            yield output_directory

    def _get_archives_dir(self, subdir: pathlib.PurePath) -> pathlib.Path:
        return pathlib.Path(self.top, subdir)


@contextmanager
def optional_contexts(
    *args: Optional[Union[_T_co, AbstractContextManager[_T_co]]],
) -> Iterator[tuple[Optional[_T_co], ...]]:
    with contextlib.ExitStack() as context_stack:
        yield tuple(
            (
                context_stack.enter_context(arg)  # pyright: ignore [reportUnknownArgumentType]
                if isinstance(arg, AbstractContextManager)
                else arg
            )
            for arg in args
        )


@contextmanager
def contextmanager_bind(
    cm_a: AbstractContextManager[_T_co],
    a_to_cm_b: Callable[[_T_co], AbstractContextManager[_T_contra]],
    /,
) -> Iterator[_T_contra]:
    with cm_a as a:
        with a_to_cm_b(a) as b:
            yield b


def os_walk_strict(
    top: StrPath, topdown: bool = True, followlinks: bool = False
) -> Iterator[tuple[str, list[str], list[str]]]:
    def onerror(exception: OSError) -> None:
        raise exception

    return os.walk(
        top=top,
        topdown=topdown,
        onerror=onerror,
        followlinks=followlinks,
    )


def mkdir_parents_opener(
    path: str, flags: int, mode: int = 0o777, *, dir_fd: Optional[int] = None
) -> int:
    if flags & (os.O_WRONLY | os.O_RDWR):
        pathlib.Path(path).parent.mkdir(parents=True, exist_ok=True)

    return os.open(path, flags, mode, dir_fd=dir_fd)


def make_archive(
    archive_name: str,
    *,
    root_dir: Optional[StrPath] = None,
    base_dir: Optional[StrPath] = None,
    dry_run: bool = False,
    owner: Optional[str] = None,
    group: Optional[str] = None,
    logger: object = None,
) -> str:
    archive_base_name: str
    archive_format: str
    if (archive_base_name := archive_name.removesuffix(".tar.xz")) != archive_name:
        archive_format = "xztar"
    elif (archive_base_name := archive_name.removesuffix(".zip")) != archive_name:
        archive_format = "zip"
    else:
        raise RuntimeError("Unsupported archive format")

    return shutil.make_archive(
        archive_base_name,
        archive_format,
        root_dir=root_dir,
        base_dir=base_dir,
        dry_run=dry_run,
        owner=owner,
        group=group,
        logger=logger,
    )


def path_re_glob(path: pathlib.Path, pattern: re.Pattern[str]) -> Iterable[pathlib.Path]:
    return (path for path in path.iterdir() if pattern.fullmatch(path.name))

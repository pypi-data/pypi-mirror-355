# SPDX-FileCopyrightText: b5327157 <b5327157@protonmail.com>
#
# SPDX-License-Identifier: LGPL-3.0-or-later

import pathlib

from collections.abc import Iterator, Sequence
from typing import Optional

from no_vtf.typing import mypyc_attr


@mypyc_attr(allow_interpreted_subclasses=True)
class InputPaths:
    def __init__(self, paths: Sequence[pathlib.Path]) -> None:
        self._paths: dict[pathlib.Path, Optional[pathlib.Path]] = dict.fromkeys(
            path.absolute() for path in paths
        )

    def __iter__(self) -> Iterator[tuple[pathlib.Path, Optional[pathlib.Path]]]:
        return iter(self._paths.items())

    def __len__(self) -> int:
        return len(self._paths)

    def has_directories(self) -> bool:
        return any(path.is_dir() for path in self._paths)

    def search_in_directories(
        self, pattern: str, *, add_results: bool = False
    ) -> Iterator[pathlib.Path]:
        results: dict[pathlib.Path, Optional[pathlib.Path]] = {}

        for path in self._paths:
            if not path.is_dir():
                continue

            for matching_path in path.rglob(pattern):
                if matching_path.is_dir():
                    continue

                if matching_path not in results:
                    yield matching_path

                self._merge(results, matching_path, path)

        if add_results:
            for path, origin_path in results.items():
                self._merge(self._paths, path, origin_path)

    def remove_directories(self) -> None:
        self._paths = {
            path: origin_path for path, origin_path in self._paths.items() if not path.is_dir()
        }

    @staticmethod
    def _merge(
        paths: dict[pathlib.Path, Optional[pathlib.Path]],
        path: pathlib.Path,
        origin_path: Optional[pathlib.Path],
    ) -> None:
        if path not in paths:
            paths[path] = origin_path
        elif origin_path:
            existing_path = paths[path]
            if not existing_path or len(origin_path.parts) < len(existing_path.parts):
                paths[path] = origin_path

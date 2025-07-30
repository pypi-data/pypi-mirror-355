# SPDX-FileCopyrightText: b5327157 <b5327157@protonmail.com>
#
# SPDX-License-Identifier: LGPL-3.0-or-later

import pathlib

from typing import Final, Optional

from no_vtf.typing import mypyc_attr


@mypyc_attr(allow_interpreted_subclasses=True)
class OutputDirectories:
    def __init__(self, output_base_directory: Optional[pathlib.Path]) -> None:
        self.output_base_directory: Final = output_base_directory

    def __call__(
        self, input_file: pathlib.Path, input_base_directory: Optional[pathlib.Path]
    ) -> pathlib.Path:
        output_directory: pathlib.Path
        if not self.output_base_directory:
            output_directory = input_file.parent
        elif not input_base_directory:
            output_directory = self.output_base_directory
        else:
            file_relative_to_directory = input_file.relative_to(input_base_directory)
            output_directory = self.output_base_directory / file_relative_to_directory.parent
        return output_directory

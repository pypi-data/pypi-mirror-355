# SPDX-FileCopyrightText: b5327157 <b5327157@protonmail.com>
#
# SPDX-License-Identifier: LGPL-3.0-or-later

from typing import TYPE_CHECKING

if TYPE_CHECKING:
    from mypy_extensions import mypyc_attr as mypyc_attr
else:
    from collections.abc import Callable
    from typing import TypeVar

    _T = TypeVar("_T")

    def mypyc_attr(*attrs: str, **kwattrs: object) -> Callable[[_T], _T]:
        return lambda x: x

# SPDX-FileCopyrightText: b5327157 <b5327157@protonmail.com>
#
# SPDX-License-Identifier: LGPL-3.0-or-later

from typing import TYPE_CHECKING

if TYPE_CHECKING:
    __version__ = "TYPE_CHECKING"
else:
    try:
        from ._version import version as __version__
    except ImportError:
        __version__ = "UNKNOWN"

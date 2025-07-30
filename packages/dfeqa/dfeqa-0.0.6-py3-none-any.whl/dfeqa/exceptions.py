from __future__ import annotations

from typing import Any


class UsageError(Exception):
    """To indicate a command-line usage error"""

    def __init__(self, *a: Any, **kw: Any):
        self.print_help = kw.pop("print_help", True)
        super().__init__(*a, **kw)

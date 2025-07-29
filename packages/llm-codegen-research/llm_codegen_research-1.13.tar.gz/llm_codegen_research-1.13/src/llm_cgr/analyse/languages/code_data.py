"""Define the CodeData class, to store code analysis data."""

from dataclasses import dataclass
from typing import Iterable


@dataclass
class CodeData:
    """
    A class to hold code analysis data.
    """

    valid: bool | None
    error: str | None
    defined_funcs: list[str]
    called_funcs: list[str]
    stdlibs: list[str]
    packages: list[str]
    imports: list[str]

    def __init__(
        self,
        valid: bool | None = None,
        error: str | None = None,
        defined_funcs: Iterable | None = None,
        called_funcs: Iterable | None = None,
        stdlibs: Iterable | None = None,
        packages: Iterable | None = None,
        imports: Iterable | None = None,
    ):
        self.valid = valid
        self.error = error
        self.defined_funcs = sorted(defined_funcs) if defined_funcs else []
        self.called_funcs = sorted(called_funcs) if called_funcs else []
        self.stdlibs = self._format_list(stdlibs) if stdlibs else []
        self.packages = self._format_list(packages) if packages else []
        self.imports = sorted(imports) if imports else []

    def _format_list(self, _list: Iterable[str]) -> list[str]:
        """
        Format a list of strings for consistency.
        """
        return sorted(set(_l.lower() for _l in _list))

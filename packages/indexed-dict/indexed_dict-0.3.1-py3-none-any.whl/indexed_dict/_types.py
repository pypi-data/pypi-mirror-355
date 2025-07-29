"""Internal type definitions for IndexedDict."""

import sys
from collections.abc import (
    Callable,
    ItemsView,
    Iterable,
    Iterator,
    KeysView,
    Mapping,
    MutableMapping,
    ValuesView,
)
from typing import TYPE_CHECKING, Any, Generic, TypeVar

if sys.version_info < (3, 11):
    from typing_extensions import Self
else:
    from typing import Self

K = TypeVar("K")
V = TypeVar("V")

__all__ = [
    "K",
    "V",
    "Any",
    "Self",
    "Mapping",
    "MutableMapping",
    "Callable",
    "Generic",
    "Iterator",
    "Iterable",
    "KeysView",
    "ValuesView",
    "ItemsView",
    "TYPE_CHECKING",
]

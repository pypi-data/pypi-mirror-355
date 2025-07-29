"""Internal view classes for IndexedDict."""

from indexed_dict._types import (
    TYPE_CHECKING,
    ItemsView,
    Iterator,
    K,
    KeysView,
    V,
    ValuesView,
)

if TYPE_CHECKING:
    from indexed_dict.indexed_dict import IndexedDict

__all__ = [
    "_IndexedDictKeysView",
    "_IndexedDictValuesView",
    "_IndexedDictItemsView",
]


class _IndexedDictKeysView(KeysView[K]):
    """Internal keys view for IndexedDict maintaining insertion order."""

    def __init__(self, indexed_dict: "IndexedDict[K, V]"):
        self._indexed_dict = indexed_dict

    def __contains__(self, key: object) -> bool:
        return key in self._indexed_dict._dict

    def __iter__(self) -> Iterator[K]:
        return iter(self._indexed_dict._index)

    def __len__(self) -> int:
        return len(self._indexed_dict._index)


class _IndexedDictValuesView(ValuesView[V]):
    """Internal values view for IndexedDict maintaining insertion order."""

    def __init__(self, indexed_dict: "IndexedDict[K, V]"):
        self._indexed_dict = indexed_dict

    def __contains__(self, value: object) -> bool:
        return any(
            self._indexed_dict._dict[k].value == value
            for k in self._indexed_dict._index
        )

    def __iter__(self) -> Iterator[V]:
        for k in self._indexed_dict._index:
            yield self._indexed_dict._dict[k].value

    def __len__(self) -> int:
        return len(self._indexed_dict._index)


class _IndexedDictItemsView(ItemsView[K, V]):
    """Internal items view for IndexedDict maintaining insertion order."""

    def __init__(self, indexed_dict: "IndexedDict[K, V]"):
        self._indexed_dict = indexed_dict

    def __contains__(self, item: object) -> bool:
        if not isinstance(item, tuple) or len(item) != 2:
            return False
        key, value = item
        return (
            key in self._indexed_dict._dict
            and self._indexed_dict._dict[key].value == value
        )

    def __iter__(self) -> Iterator[tuple[K, V]]:
        for k in self._indexed_dict._index:
            yield (k, self._indexed_dict._dict[k].value)

    def __len__(self) -> int:
        return len(self._indexed_dict._index)

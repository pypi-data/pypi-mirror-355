import pytest
from indexed_dict import IndexedDict


def test_reversed_yields_keys_in_reverse_order():
    d = IndexedDict([("a", 1), ("b", 2), ("c", 3)])
    assert list(reversed(d)) == ["c", "b", "a"]


def test_reversed_with_empty_dict():
    d = IndexedDict()
    assert list(reversed(d)) == []

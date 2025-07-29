import pytest
from indexed_dict import IndexedDict


def test_iter_yields_keys_in_order():
    d = IndexedDict([("c", 3), ("a", 1), ("b", 2)])
    assert list(iter(d)) == ["c", "a", "b"]

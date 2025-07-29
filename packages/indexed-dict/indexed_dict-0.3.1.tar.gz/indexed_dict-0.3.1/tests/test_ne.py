import pytest
from indexed_dict import IndexedDict


def test_ne_opposite_of_eq():
    d1 = IndexedDict({"a": 1, "b": 2})
    d2 = IndexedDict({"a": 1, "b": 2})
    d3 = IndexedDict({"a": 1, "c": 3})

    assert not (d1 != d2)
    assert d1 != d3

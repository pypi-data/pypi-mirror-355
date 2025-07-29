import pytest
from indexed_dict import IndexedDict


def test_getitem_key():
    d = IndexedDict({"a": 1, "b": 2, "c": 3})
    assert d["a"] == 1
    assert d["b"] == 2
    assert d["c"] == 3


def test_getitem_missing_key():
    d = IndexedDict({"a": 1, "b": 2})
    with pytest.raises(KeyError):
        d["z"]


def test_getitem_slice():
    d = IndexedDict({"a": 1, "b": 2, "c": 3, "d": 4, "e": 5})
    assert d[1:4] == [2, 3, 4]
    assert d[:2] == [1, 2]
    assert d[3:] == [4, 5]
    assert d[:] == [1, 2, 3, 4, 5]
    assert d[::2] == [1, 3, 5]
    assert d[::-1] == [5, 4, 3, 2, 1]


def test_getitem_slice_empty():
    d = IndexedDict()
    assert d[:] == []

import pytest
from indexed_dict import IndexedDict


def test_setitem_key():
    d = IndexedDict()
    d["a"] = 1
    assert d["a"] == 1
    assert list(d.keys()) == ["a"]
    assert list(d.values()) == [1]


def test_setitem_update_key():
    d = IndexedDict({"a": 1, "b": 2})
    d["a"] = 10
    assert d["a"] == 10
    assert list(d.keys()) == ["a", "b"]
    assert list(d.values()) == [10, 2]


def test_setitem_slice():
    d = IndexedDict({"a": 1, "b": 2, "c": 3})
    d[0:2] = [10, 20]
    assert d["a"] == 10
    assert d["b"] == 20
    assert d["c"] == 3
    assert list(d.keys()) == ["a", "b", "c"]
    assert list(d.values()) == [10, 20, 3]


def test_setitem_slice_all():
    d = IndexedDict({"a": 1, "b": 2, "c": 3})
    d[:] = [4, 5, 6]
    assert d["a"] == 4
    assert d["b"] == 5
    assert d["c"] == 6
    assert list(d.keys()) == ["a", "b", "c"]
    assert list(d.values()) == [4, 5, 6]


def test_setitem_slice_error_length_mismatch():
    d = IndexedDict({"a": 1, "b": 2, "c": 3})
    with pytest.raises(ValueError):
        d[0:2] = [10]  # Not enough values
    with pytest.raises(ValueError):
        d[0:2] = [10, 20, 30]  # Too many values


def test_setitem_slice_error_not_iterable():
    d = IndexedDict({"a": 1, "b": 2, "c": 3})
    with pytest.raises(TypeError):
        d[0:2] = 10  # Not an iterable
    with pytest.raises(TypeError):
        # A string is iterable but not valid for slice assignment
        d[0:2] = "ab"

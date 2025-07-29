import pytest
from indexed_dict import IndexedDict


def test_ior_updates_in_place():
    d1 = IndexedDict({"a": 1, "b": 2})
    d2 = IndexedDict({"c": 3, "d": 4})
    d1.__ior__(d2)

    assert d1 == IndexedDict({"a": 1, "b": 2, "c": 3, "d": 4})


def test_ior_with_overlap_uses_right_value():
    d1 = IndexedDict({"a": 1, "b": 2})
    d2 = IndexedDict({"b": 20, "c": 3})
    d1.__ior__(d2)

    assert d1["b"] == 20
    assert d1 == IndexedDict({"a": 1, "b": 20, "c": 3})


def test_ior_returns_self():
    d1 = IndexedDict({"a": 1, "b": 2})
    d2 = IndexedDict({"c": 3})
    result = d1.__ior__(d2)

    assert result is d1


def test_ior_with_regular_dict():
    d1 = IndexedDict({"a": 1, "b": 2})
    d2 = {"c": 3, "d": 4}
    d1.__ior__(d2)

    assert d1 == IndexedDict({"a": 1, "b": 2, "c": 3, "d": 4})

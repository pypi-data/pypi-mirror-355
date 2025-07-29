import pytest
from indexed_dict import IndexedDict


def test_eq_with_same_indexeddict():
    d1 = IndexedDict({"a": 1, "b": 2})
    d2 = IndexedDict({"a": 1, "b": 2})
    assert d1 == d2


def test_eq_with_different_values():
    d1 = IndexedDict({"a": 1, "b": 2})
    d2 = IndexedDict({"a": 1, "b": 3})
    assert d1 != d2


def test_eq_with_different_keys():
    d1 = IndexedDict({"a": 1, "b": 2})
    d2 = IndexedDict({"a": 1, "c": 2})
    assert d1 != d2


def test_eq_with_different_order():
    d1 = IndexedDict([("a", 1), ("b", 2)])
    d2 = IndexedDict([("b", 2), ("a", 1)])
    assert d1 != d2


def test_eq_with_regular_dict():
    d1 = IndexedDict({"a": 1, "b": 2})
    d2 = {"a": 1, "b": 2}
    assert d1 == d2


def test_eq_with_non_dict():
    d = IndexedDict({"a": 1, "b": 2})
    assert d != "not a dict"
    assert d != 42
    assert d != [("a", 1), ("b", 2)]

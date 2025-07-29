import pytest
from indexed_dict import IndexedDict


def test_copy_returns_new_instance():
    d1 = IndexedDict({"a": 1, "b": 2})
    d2 = d1.copy()
    assert d1 is not d2


def test_copy_preserves_content():
    d1 = IndexedDict({"a": 1, "b": 2})
    d2 = d1.copy()
    assert d1 == d2


def test_copy_preserves_order():
    d1 = IndexedDict([("c", 3), ("a", 1), ("b", 2)])
    d2 = d1.copy()
    assert list(d1.keys()) == list(d2.keys())


def test_copy_is_shallow():
    nested = [1, 2, 3]
    d1 = IndexedDict({"a": 1, "list": nested})
    d2 = d1.copy()
    nested.append(4)
    assert d2["list"] == [1, 2, 3, 4]  # Changed in both

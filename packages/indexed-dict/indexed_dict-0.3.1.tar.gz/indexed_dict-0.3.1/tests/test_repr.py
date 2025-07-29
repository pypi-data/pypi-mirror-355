import pytest
from indexed_dict import IndexedDict


def test_repr_shows_class_and_contents():
    d = IndexedDict({"a": 1, "b": 2})
    r = repr(d)
    assert r.startswith("IndexedDict(")
    assert "a" in r and "1" in r
    assert "b" in r and "2" in r


def test_repr_with_empty_dict():
    d = IndexedDict()
    assert repr(d) == "IndexedDict({})"

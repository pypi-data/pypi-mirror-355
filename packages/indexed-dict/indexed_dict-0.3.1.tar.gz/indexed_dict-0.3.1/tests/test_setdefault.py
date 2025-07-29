import pytest
from indexed_dict import IndexedDict


def test_setdefault_returns_existing_value():
    d = IndexedDict({"a": 1, "b": 2})
    assert d.setdefault("a", 42) == 1


def test_setdefault_does_not_change_existing_key():
    d = IndexedDict({"a": 1, "b": 2})
    d.setdefault("a", 42)
    assert d["a"] == 1


def test_setdefault_adds_missing_key():
    d = IndexedDict({"a": 1})
    assert d.setdefault("b", 2) == 2
    assert "b" in d
    assert d["b"] == 2


def test_setdefault_with_none_default():
    d = IndexedDict({"a": 1})
    assert d.setdefault("b") is None
    assert d["b"] is None

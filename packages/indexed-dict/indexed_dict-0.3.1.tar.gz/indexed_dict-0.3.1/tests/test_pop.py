import pytest
from indexed_dict import IndexedDict


def test_pop_returns_value():
    d = IndexedDict({"a": 1, "b": 2})
    assert d.pop("a") == 1


def test_pop_removes_key():
    d = IndexedDict({"a": 1, "b": 2})
    d.pop("a")
    assert "a" not in d
    assert len(d) == 1


def test_pop_with_default_for_missing_key():
    d = IndexedDict({"a": 1})
    assert d.pop("z", 42) == 42


def test_pop_raises_key_error_for_missing_key():
    d = IndexedDict({"a": 1})
    with pytest.raises(KeyError):
        d.pop("z")

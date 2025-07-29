import pytest
from indexed_dict import IndexedDict


def test_keys_returns_key_view():
    d = IndexedDict({"a": 1, "b": 2, "c": 3})
    keys = d.keys()
    assert "a" in keys
    assert "z" not in keys


def test_keys_reflects_changes():
    d = IndexedDict({"a": 1, "b": 2})
    keys = d.keys()
    d["c"] = 3
    assert "c" in keys
    del d["a"]
    assert "a" not in keys

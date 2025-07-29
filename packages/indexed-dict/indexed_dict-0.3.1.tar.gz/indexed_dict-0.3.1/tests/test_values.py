import pytest
from indexed_dict import IndexedDict


def test_values_returns_value_view():
    d = IndexedDict({"a": 1, "b": 2, "c": 3})
    values = d.values()
    assert 1 in values
    assert 42 not in values


def test_values_reflects_changes():
    d = IndexedDict({"a": 1, "b": 2})
    values = d.values()
    d["c"] = 3
    assert 3 in values
    del d["a"]
    assert 1 not in values

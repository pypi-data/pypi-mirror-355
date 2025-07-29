import pytest
from indexed_dict import IndexedDict


def test_clear_removes_all_items():
    d = IndexedDict({"a": 1, "b": 2, "c": 3})
    d.clear()
    assert len(d) == 0
    assert list(d.keys()) == []
    assert list(d.values()) == []


def test_clear_on_empty_dict():
    d = IndexedDict()
    d.clear()  # Should not raise error
    assert len(d) == 0

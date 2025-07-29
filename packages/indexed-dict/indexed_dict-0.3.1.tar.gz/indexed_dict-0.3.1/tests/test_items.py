import pytest
from indexed_dict import IndexedDict


def test_items_returns_item_view():
    d = IndexedDict({"a": 1, "b": 2})
    items = d.items()
    assert ("a", 1) in items
    assert ("z", 26) not in items


def test_items_reflects_changes():
    d = IndexedDict({"a": 1, "b": 2})
    items = d.items()
    d["c"] = 3
    assert ("c", 3) in items
    del d["a"]
    assert ("a", 1) not in items

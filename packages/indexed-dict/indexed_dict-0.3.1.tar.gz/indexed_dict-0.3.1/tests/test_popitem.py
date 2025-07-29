import pytest
from indexed_dict import IndexedDict


def test_popitem_returns_key_value_pair():
    d = IndexedDict({"a": 1, "b": 2})
    item = d.popitem()
    assert isinstance(item, tuple)
    assert len(item) == 2


def test_popitem_removes_last_item():
    d = IndexedDict({"a": 1, "b": 2, "c": 3})
    key, value = d.popitem()
    assert key == "c"
    assert value == 3
    assert key not in d


def test_popitem_raises_key_error_for_empty_dict():
    d = IndexedDict()
    with pytest.raises(KeyError):
        d.popitem()

import pytest
from indexed_dict import IndexedDict


def test_fromitems_with_dict():
    result = IndexedDict.fromitems({"a": 1, "b": 2})
    assert isinstance(result, IndexedDict)
    assert result["a"] == 1
    assert result["b"] == 2


def test_fromitems_with_items():
    result = IndexedDict.fromitems([("a", 1), ("b", 2)])
    assert isinstance(result, IndexedDict)
    assert result["a"] == 1
    assert result["b"] == 2


def test_fromitems_preserves_order_of_items():
    result = IndexedDict.fromitems([("c", 3), ("a", 1), ("b", 2)])
    assert list(result.keys()) == ["c", "a", "b"]

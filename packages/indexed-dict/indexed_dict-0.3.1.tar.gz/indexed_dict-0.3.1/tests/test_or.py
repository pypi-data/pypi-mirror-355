import pytest
from indexed_dict import IndexedDict


def test_or_combines_dicts():
    d1 = IndexedDict({"a": 1, "b": 2})
    d2 = IndexedDict({"c": 3, "d": 4})
    result = d1.__or__(d2)

    assert isinstance(result, IndexedDict)
    assert result == IndexedDict({"a": 1, "b": 2, "c": 3, "d": 4})


def test_or_with_overlap_uses_right_value():
    d1 = IndexedDict({"a": 1, "b": 2})
    d2 = IndexedDict({"b": 20, "c": 3})
    result = d1.__or__(d2)

    assert result["b"] == 20
    assert result == IndexedDict({"a": 1, "b": 20, "c": 3})


def test_or_preserves_original_dicts():
    d1 = IndexedDict({"a": 1, "b": 2})
    d2 = IndexedDict({"c": 3, "d": 4})
    _ = d1.__or__(d2)

    assert d1 == IndexedDict({"a": 1, "b": 2})
    assert d2 == IndexedDict({"c": 3, "d": 4})


def test_or_with_regular_dict():
    d1 = IndexedDict({"a": 1, "b": 2})
    d2 = {"c": 3, "d": 4}
    result = d1.__or__(d2)

    assert isinstance(result, IndexedDict)
    assert result == IndexedDict({"a": 1, "b": 2, "c": 3, "d": 4})

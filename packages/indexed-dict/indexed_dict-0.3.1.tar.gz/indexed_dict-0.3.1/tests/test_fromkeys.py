import pytest
from indexed_dict import IndexedDict


def test_fromkeys_creates_dict_with_iterable():
    result = IndexedDict.fromkeys(["a", "b", "c"])
    assert isinstance(result, IndexedDict)
    assert list(result.keys()) == ["a", "b", "c"]


def test_fromkeys_uses_none_as_default_value():
    result = IndexedDict.fromkeys(["a", "b"])
    assert result["a"] is None
    assert result["b"] is None


def test_fromkeys_with_custom_value():
    result = IndexedDict.fromkeys(["a", "b"], 42)
    assert result["a"] == 42
    assert result["b"] == 42


def test_fromkeys_with_empty_iterable():
    result = IndexedDict.fromkeys([])
    assert len(result) == 0

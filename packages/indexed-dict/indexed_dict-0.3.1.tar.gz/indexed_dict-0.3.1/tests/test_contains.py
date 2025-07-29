import pytest
from indexed_dict import IndexedDict


def test_contains_with_existing_key():
    d = IndexedDict({"a": 1, "b": 2})
    assert "a" in d
    assert "b" in d


def test_contains_with_missing_key():
    d = IndexedDict({"a": 1, "b": 2})
    assert "c" not in d
    assert 42 not in d

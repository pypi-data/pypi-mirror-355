import pytest
from indexed_dict import IndexedDict


class TestSort:
    def test_sort_by_key(self):
        d = IndexedDict({"c": 3, "a": 1, "b": 2})
        d.sort()
        assert list(d.keys()) == ["a", "b", "c"]
        assert list(d.values()) == [1, 2, 3]

    def test_sort_with_custom_key(self):
        d = IndexedDict({"apple": 5, "banana": 6, "carrot": 3})
        d.sort(key=len)  # Sort by length of key
        assert list(d.keys()) == ["apple", "banana", "carrot"]

    def test_sort_with_reverse(self):
        d = IndexedDict({"a": 1, "b": 2, "c": 3})
        d.sort(reverse=True)
        assert list(d.keys()) == ["c", "b", "a"]

    def test_sort_with_custom_key_and_reverse(self):
        d = IndexedDict({"apple": 5, "banana": 6, "carrot": 3})
        d.sort(key=len, reverse=True)  # Sort by length of key, descending
        assert list(d.keys()) == ["banana", "carrot", "apple"]

    def test_sort_empty_dict(self):
        d = IndexedDict()
        d.sort()  # Should not raise an error
        assert list(d.keys()) == []

    def test_sort_single_item(self):
        d = IndexedDict({"a": 1})
        d.sort()
        assert list(d.keys()) == ["a"]

    def test_sort_preserves_values(self):
        d = IndexedDict({"c": 30, "a": 10, "b": 20})
        d.sort()
        assert d["a"] == 10
        assert d["b"] == 20
        assert d["c"] == 30

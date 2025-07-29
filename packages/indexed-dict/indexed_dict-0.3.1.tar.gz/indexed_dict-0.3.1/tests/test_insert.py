import pytest
from indexed_dict import IndexedDict


class TestInsert:
    def test_insert_at_beginning(self):
        d = IndexedDict({"a": 1, "b": 2})
        d.insert(0, "c", 3)
        assert list(d.keys()) == ["c", "a", "b"]
        assert d["c"] == 3
        assert len(d) == 3

    def test_insert_in_middle(self):
        d = IndexedDict({"a": 1, "b": 2, "c": 3})
        d.insert(1, "d", 4)
        assert list(d.keys()) == ["a", "d", "b", "c"]
        assert d["d"] == 4

    def test_insert_at_end(self):
        d = IndexedDict({"a": 1, "b": 2})
        d.insert(2, "c", 3)
        assert list(d.keys()) == ["a", "b", "c"]
        assert d["c"] == 3

    def test_insert_with_negative_index(self):
        d = IndexedDict({"a": 1, "b": 2, "c": 3})
        d.insert(-1, "d", 4)
        assert list(d.keys()) == ["a", "b", "d", "c"]

    def test_insert_with_large_index_appends(self):
        d = IndexedDict({"a": 1, "b": 2})
        d.insert(10, "c", 3)
        assert list(d.keys()) == ["a", "b", "c"]

    def test_insert_with_large_negative_index_prepends(self):
        d = IndexedDict({"a": 1, "b": 2})
        d.insert(-10, "c", 3)
        assert list(d.keys()) == ["c", "a", "b"]

    def test_insert_raises_key_error_for_existing_key(self):
        d = IndexedDict({"a": 1, "b": 2})
        with pytest.raises(KeyError):
            d.insert(0, "a", 3)

import pytest
from indexed_dict import IndexedDict


class TestIndexedDictDelItem:
    def test_delitem_key(self):
        d = IndexedDict({"a": 1, "b": 2, "c": 3})
        del d["b"]
        assert len(d) == 2
        assert list(d.keys()) == ["a", "c"]
        assert list(d.values()) == [1, 3]
        with pytest.raises(KeyError):
            d["b"]

    def test_delitem_missing_key(self):
        d = IndexedDict({"a": 1, "b": 2})
        with pytest.raises(KeyError):
            del d["z"]

    def test_delitem_slice(self):
        d = IndexedDict({"a": 1, "b": 2, "c": 3, "d": 4, "e": 5})
        del d[1:4]  # Delete b, c, d
        assert len(d) == 2
        assert list(d.keys()) == ["a", "e"]
        assert list(d.values()) == [1, 5]

    def test_delitem_slice_empty(self):
        d = IndexedDict()
        del d[:]  # No effect on empty dict
        assert len(d) == 0

    def test_delitem_slice_all(self):
        d = IndexedDict({"a": 1, "b": 2, "c": 3})
        del d[:]
        assert len(d) == 0
        assert not list(d.keys())
        assert not list(d.values())

    def test_delitem_slice_start(self):
        d = IndexedDict({"a": 1, "b": 2, "c": 3, "d": 4})
        del d[:2]  # Delete a, b
        assert len(d) == 2
        assert list(d.keys()) == ["c", "d"]
        assert list(d.values()) == [3, 4]

    def test_delitem_slice_end(self):
        d = IndexedDict({"a": 1, "b": 2, "c": 3, "d": 4})
        del d[2:]  # Delete c, d
        assert len(d) == 2
        assert list(d.keys()) == ["a", "b"]
        assert list(d.values()) == [1, 2]

    def test_delitem_slice_step(self):
        d = IndexedDict({"a": 1, "b": 2, "c": 3, "d": 4, "e": 5})
        del d[::2]  # Delete a, c, e
        assert len(d) == 2
        assert list(d.keys()) == ["b", "d"]
        assert list(d.values()) == [2, 4]

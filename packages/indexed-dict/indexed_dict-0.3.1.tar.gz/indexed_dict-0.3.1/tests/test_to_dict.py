import pytest
from indexed_dict import IndexedDict


class TestToDict:
    def test_to_dict_returns_plain_dict(self):
        d = IndexedDict({"a": 1, "b": 2, "c": 3})
        result = d.to_dict()
        assert isinstance(result, dict)
        assert not isinstance(result, IndexedDict)

    def test_to_dict_preserves_values(self):
        d = IndexedDict({"a": 1, "b": 2, "c": 3})
        result = d.to_dict()
        assert result == {"a": 1, "b": 2, "c": 3}

    def test_to_dict_preserves_order(self):
        d = IndexedDict([("c", 3), ("a", 1), ("b", 2)])
        result = d.to_dict()
        assert list(result.keys()) == ["c", "a", "b"]

    def test_to_dict_empty(self):
        d = IndexedDict()
        result = d.to_dict()
        assert result == {}

import pytest
from indexed_dict import IndexedDict


class TestPopFromIndex:
    def test_pop_from_index_returns_correct_value(self):
        d = IndexedDict({"a": 1, "b": 2, "c": 3})
        assert d.pop_from_index(1) == 2

    def test_pop_from_index_removes_item(self):
        d = IndexedDict({"a": 1, "b": 2, "c": 3})
        d.pop_from_index(1)
        assert "b" not in d
        assert len(d) == 2
        assert list(d.keys()) == ["a", "c"]

    def test_pop_from_index_with_negative_index(self):
        d = IndexedDict({"a": 1, "b": 2, "c": 3})
        assert d.pop_from_index(-1) == 3
        assert "c" not in d
        assert len(d) == 2

    def test_pop_from_index_raises_index_error_for_empty_dict(self):
        d = IndexedDict()
        with pytest.raises(IndexError):
            d.pop_from_index(0)

    def test_pop_from_index_raises_index_error_for_out_of_range(self):
        d = IndexedDict({"a": 1, "b": 2})
        with pytest.raises(IndexError):
            d.pop_from_index(2)

        with pytest.raises(IndexError):
            d.pop_from_index(-3)

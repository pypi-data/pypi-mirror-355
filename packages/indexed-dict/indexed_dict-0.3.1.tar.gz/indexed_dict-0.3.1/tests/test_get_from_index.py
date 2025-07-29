import pytest
from indexed_dict import IndexedDict


class TestGetFromIndex:
    def test_get_from_index_returns_correct_value(self):
        d = IndexedDict({"a": 1, "b": 2, "c": 3})
        assert d.get_from_index(0) == 1
        assert d.get_from_index(1) == 2
        assert d.get_from_index(2) == 3

    def test_get_from_index_with_negative_index(self):
        d = IndexedDict({"a": 1, "b": 2, "c": 3})
        assert d.get_from_index(-1) == 3
        assert d.get_from_index(-2) == 2
        assert d.get_from_index(-3) == 1

    def test_get_from_index_raises_index_error_for_out_of_range(self):
        d = IndexedDict({"a": 1, "b": 2})
        with pytest.raises(IndexError):
            d.get_from_index(2)

        with pytest.raises(IndexError):
            d.get_from_index(-3)

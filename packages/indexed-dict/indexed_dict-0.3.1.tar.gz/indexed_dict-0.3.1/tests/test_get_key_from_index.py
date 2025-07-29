import pytest
from indexed_dict import IndexedDict


class TestGetKeyFromIndex:
    def test_get_key_from_index_returns_correct_key(self):
        d = IndexedDict({"a": 1, "b": 2, "c": 3})
        assert d.get_key_from_index(0) == "a"
        assert d.get_key_from_index(1) == "b"
        assert d.get_key_from_index(2) == "c"

    def test_get_key_from_index_with_negative_index(self):
        d = IndexedDict({"a": 1, "b": 2, "c": 3})
        assert d.get_key_from_index(-1) == "c"
        assert d.get_key_from_index(-2) == "b"
        assert d.get_key_from_index(-3) == "a"

    def test_get_key_from_index_raises_index_error_for_out_of_range(self):
        d = IndexedDict({"a": 1, "b": 2})
        with pytest.raises(IndexError):
            d.get_key_from_index(2)

        with pytest.raises(IndexError):
            d.get_key_from_index(-3)

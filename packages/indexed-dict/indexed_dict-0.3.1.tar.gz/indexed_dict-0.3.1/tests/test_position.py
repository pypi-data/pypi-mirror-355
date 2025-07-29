import pytest
from indexed_dict import IndexedDict


class TestPosition:
    def test_position_returns_correct_index(self):
        d = IndexedDict({"a": 1, "b": 2, "c": 3})
        assert d.position("a") == 0
        assert d.position("b") == 1
        assert d.position("c") == 2

    def test_position_raises_value_error_for_missing_key(self):
        d = IndexedDict({"a": 1, "b": 2})
        with pytest.raises(ValueError):
            d.position("z")

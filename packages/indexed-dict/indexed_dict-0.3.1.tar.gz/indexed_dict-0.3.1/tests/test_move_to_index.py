import pytest
from indexed_dict import IndexedDict


class TestMoveToIndex:
    def test_move_to_index_changes_position(self):
        d = IndexedDict({"a": 1, "b": 2, "c": 3})
        d.move_to_index("a", 2)
        assert list(d.keys()) == ["b", "c", "a"]

    def test_move_to_index_preserves_value(self):
        d = IndexedDict({"a": 1, "b": 2, "c": 3})
        d.move_to_index("a", 2)
        assert d["a"] == 1

    def test_move_to_beginning(self):
        d = IndexedDict({"a": 1, "b": 2, "c": 3})
        d.move_to_index("c", 0)
        assert list(d.keys()) == ["c", "a", "b"]

    def test_move_to_end(self):
        d = IndexedDict({"a": 1, "b": 2, "c": 3})
        d.move_to_index("a", 2)
        assert list(d.keys()) == ["b", "c", "a"]

    def test_move_to_same_position_no_effect(self):
        d = IndexedDict({"a": 1, "b": 2, "c": 3})
        original_order = list(d.keys())
        d.move_to_index("b", 1)
        assert list(d.keys()) == original_order

    def test_move_to_index_with_negative_index(self):
        d = IndexedDict({"a": 1, "b": 2, "c": 3})
        # For a list of 3 items, -1 is the last position (index 2)
        d.move_to_index("a", -1)
        # Expected: "a" should be last
        assert list(d.keys()) == ["b", "c", "a"]

    def test_move_to_index_with_large_index_moves_to_end(self):
        d = IndexedDict({"a": 1, "b": 2, "c": 3})
        d.move_to_index("a", 10)
        assert list(d.keys()) == ["b", "c", "a"]

    def test_move_to_index_with_large_negative_index_moves_to_beginning(self):
        d = IndexedDict({"a": 1, "b": 2, "c": 3})
        d.move_to_index("c", -10)
        assert list(d.keys()) == ["c", "a", "b"]

    def test_move_to_index_raises_key_error_for_missing_key(self):
        d = IndexedDict({"a": 1, "b": 2})
        with pytest.raises(KeyError):
            d.move_to_index("z", 0)

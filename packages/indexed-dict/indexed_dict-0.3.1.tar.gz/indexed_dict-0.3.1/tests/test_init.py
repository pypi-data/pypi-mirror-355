import pytest
from indexed_dict import IndexedDict


class TestIndexedDictInit:
    """Tests for IndexedDict initialization."""

    def test_init_empty(self):
        """Test initializing an empty IndexedDict."""
        d = IndexedDict()
        assert len(d) == 0
        assert d.to_dict() == {}
        assert list(d.keys()) == []
        assert list(d.values()) == []
        assert list(d.items()) == []

    def test_init_with_dict(self):
        """Test initializing with a dictionary."""
        d = IndexedDict({"a": 1, "b": 2, "c": 3})
        assert len(d) == 3
        assert d.to_dict() == {"a": 1, "b": 2, "c": 3}
        assert list(d.keys()) == ["a", "b", "c"]
        assert list(d.values()) == [1, 2, 3]
        assert list(d.items()) == [("a", 1), ("b", 2), ("c", 3)]

    def test_init_with_items(self):
        """Test initializing with key-value pairs."""
        d = IndexedDict([("a", 1), ("b", 2), ("c", 3)])
        assert len(d) == 3
        assert d.to_dict() == {"a": 1, "b": 2, "c": 3}
        assert list(d.keys()) == ["a", "b", "c"]
        assert list(d.values()) == [1, 2, 3]
        assert list(d.items()) == [("a", 1), ("b", 2), ("c", 3)]

    def test_init_with_kwargs(self):
        """Test initializing with keyword arguments."""
        d = IndexedDict(a=1, b=2, c=3)
        assert len(d) == 3
        assert d.to_dict() == {"a": 1, "b": 2, "c": 3}
        assert list(d.keys()) == ["a", "b", "c"]
        assert list(d.values()) == [1, 2, 3]
        assert list(d.items()) == [("a", 1), ("b", 2), ("c", 3)]

    def test_init_with_dict_and_kwargs(self):
        """Test initializing with a dictionary and keyword arguments."""
        d = IndexedDict({"a": 1, "b": 2}, c=3, d=4)
        assert len(d) == 4
        assert d.to_dict() == {"a": 1, "b": 2, "c": 3, "d": 4}
        # Check order of keys
        assert list(d.keys()) == ["a", "b", "c", "d"]

    def test_init_with_none(self):
        """Test initializing with None."""
        d = IndexedDict(None)
        assert len(d) == 0
        assert d.to_dict() == {}

    def test_init_with_empty_dict(self):
        """Test initializing with an empty dictionary."""
        d = IndexedDict({})
        assert len(d) == 0
        assert d.to_dict() == {}

    def test_init_with_empty_list(self):
        """Test initializing with an empty list."""
        d = IndexedDict([])
        assert len(d) == 0
        assert d.to_dict() == {}

    def test_init_with_duplicate_keys(self):
        """Test initializing with duplicate keys."""
        d = IndexedDict([("a", 1), ("b", 2), ("a", 3)])
        # Last value for duplicate key should be used
        assert len(d) == 2
        assert d.to_dict() == {"a": 3, "b": 2}
        # Check order of keys (the first occurrence should be preserved)
        assert list(d.keys()) == ["a", "b"]

    def test_init_with_unhashable_key(self):
        """Test initializing with an unhashable key."""
        with pytest.raises(TypeError):
            IndexedDict({[1, 2]: "unhashable"})

    def test_init_with_invalid_data(self):
        """Test initializing with invalid data."""
        with pytest.raises(TypeError):
            IndexedDict(123)  # Not a mapping or iterable

import pytest
from indexed_dict import IndexedDict


class TestKeys:
    def test_keys_returns_key_view(self):
        d = IndexedDict({"a": 1, "b": 2, "c": 3})
        keys = d.keys()
        assert "a" in keys
        assert "z" not in keys

    def test_keys_reflects_changes(self):
        d = IndexedDict({"a": 1, "b": 2})
        keys = d.keys()
        d["c"] = 3
        assert "c" in keys
        del d["a"]
        assert "a" not in keys


class TestValues:
    def test_values_returns_value_view(self):
        d = IndexedDict({"a": 1, "b": 2, "c": 3})
        values = d.values()
        assert 1 in values
        assert 42 not in values

    def test_values_reflects_changes(self):
        d = IndexedDict({"a": 1, "b": 2})
        values = d.values()
        d["c"] = 3
        assert 3 in values
        del d["a"]
        assert 1 not in values


class TestItems:
    def test_items_returns_item_view(self):
        d = IndexedDict({"a": 1, "b": 2})
        items = d.items()
        assert ("a", 1) in items
        assert ("z", 26) not in items

    def test_items_reflects_changes(self):
        d = IndexedDict({"a": 1, "b": 2})
        items = d.items()
        d["c"] = 3
        assert ("c", 3) in items
        del d["a"]
        assert ("a", 1) not in items


class TestClear:
    def test_clear_removes_all_items(self):
        d = IndexedDict({"a": 1, "b": 2, "c": 3})
        d.clear()
        assert len(d) == 0
        assert list(d.keys()) == []
        assert list(d.values()) == []

    def test_clear_on_empty_dict(self):
        d = IndexedDict()
        d.clear()  # Should not raise error
        assert len(d) == 0


class TestCopy:
    def test_copy_returns_new_instance(self):
        d1 = IndexedDict({"a": 1, "b": 2})
        d2 = d1.copy()
        assert d1 is not d2

    def test_copy_preserves_content(self):
        d1 = IndexedDict({"a": 1, "b": 2})
        d2 = d1.copy()
        assert d1 == d2

    def test_copy_preserves_order(self):
        d1 = IndexedDict([("c", 3), ("a", 1), ("b", 2)])
        d2 = d1.copy()
        assert list(d1.keys()) == list(d2.keys())

    def test_copy_is_shallow(self):
        nested = [1, 2, 3]
        d1 = IndexedDict({"a": 1, "list": nested})
        d2 = d1.copy()
        nested.append(4)
        assert d2["list"] == [1, 2, 3, 4]  # Changed in both


class TestPop:
    def test_pop_returns_value(self):
        d = IndexedDict({"a": 1, "b": 2})
        assert d.pop("a") == 1

    def test_pop_removes_key(self):
        d = IndexedDict({"a": 1, "b": 2})
        d.pop("a")
        assert "a" not in d
        assert len(d) == 1

    def test_pop_with_default_for_missing_key(self):
        d = IndexedDict({"a": 1})
        assert d.pop("z", 42) == 42

    def test_pop_raises_key_error_for_missing_key(self):
        d = IndexedDict({"a": 1})
        with pytest.raises(KeyError):
            d.pop("z")


class TestPopitem:
    def test_popitem_returns_key_value_pair(self):
        d = IndexedDict({"a": 1, "b": 2})
        item = d.popitem()
        assert isinstance(item, tuple)
        assert len(item) == 2

    def test_popitem_removes_last_item(self):
        d = IndexedDict({"a": 1, "b": 2, "c": 3})
        key, value = d.popitem()
        assert key == "c"
        assert value == 3
        assert key not in d

    def test_popitem_raises_key_error_for_empty_dict(self):
        d = IndexedDict()
        with pytest.raises(KeyError):
            d.popitem()


class TestSetdefault:
    def test_setdefault_returns_existing_value(self):
        d = IndexedDict({"a": 1, "b": 2})
        assert d.setdefault("a", 42) == 1

    def test_setdefault_does_not_change_existing_key(self):
        d = IndexedDict({"a": 1, "b": 2})
        d.setdefault("a", 42)
        assert d["a"] == 1

    def test_setdefault_adds_missing_key(self):
        d = IndexedDict({"a": 1})
        assert d.setdefault("b", 2) == 2
        assert "b" in d
        assert d["b"] == 2

    def test_setdefault_with_none_default(self):
        d = IndexedDict({"a": 1})
        assert d.setdefault("b") is None
        assert d["b"] is None


class TestUpdate:
    def test_update_with_dict(self):
        d = IndexedDict({"a": 1, "b": 2})
        d.update({"b": 20, "c": 3})
        assert d["a"] == 1
        assert d["b"] == 20
        assert d["c"] == 3

    def test_update_with_items(self):
        d = IndexedDict({"a": 1, "b": 2})
        d.update([("b", 20), ("c", 3)])
        assert d["a"] == 1
        assert d["b"] == 20
        assert d["c"] == 3

    def test_update_with_kwargs(self):
        d = IndexedDict({"a": 1, "b": 2})
        d.update(b=20, c=3)
        assert d["a"] == 1
        assert d["b"] == 20
        assert d["c"] == 3

    def test_update_with_dict_and_kwargs(self):
        d = IndexedDict({"a": 1, "b": 2})
        d.update({"b": 20}, c=3, d=4)
        assert d["a"] == 1
        assert d["b"] == 20
        assert d["c"] == 3
        assert d["d"] == 4

    def test_update_adds_new_keys_at_end(self):
        d = IndexedDict({"a": 1, "b": 2})
        d.update({"c": 3, "d": 4})
        assert list(d.keys()) == ["a", "b", "c", "d"]

    def test_update_with_empty_dict(self):
        d = IndexedDict({"a": 1, "b": 2})
        d.update({})
        assert d["a"] == 1
        assert d["b"] == 2

    def test_update_raises_type_error_for_invalid_arg(self):
        d = IndexedDict()
        with pytest.raises(TypeError):
            d.update(42)

    def test_update_raises_type_error_for_multiple_positional_args(self):
        d = IndexedDict()
        with pytest.raises(TypeError):
            d.update({}, {})


class TestFromkeys:
    def test_fromkeys_creates_dict_with_iterable(self):
        result = IndexedDict.fromkeys(["a", "b", "c"])
        assert isinstance(result, IndexedDict)
        assert list(result.keys()) == ["a", "b", "c"]

    def test_fromkeys_uses_none_as_default_value(self):
        result = IndexedDict.fromkeys(["a", "b"])
        assert result["a"] is None
        assert result["b"] is None

    def test_fromkeys_with_custom_value(self):
        result = IndexedDict.fromkeys(["a", "b"], 42)
        assert result["a"] == 42
        assert result["b"] == 42

    def test_fromkeys_with_empty_iterable(self):
        result = IndexedDict.fromkeys([])
        assert len(result) == 0


class TestFromitems:
    def test_fromitems_with_dict(self):
        result = IndexedDict.fromitems({"a": 1, "b": 2})
        assert isinstance(result, IndexedDict)
        assert result["a"] == 1
        assert result["b"] == 2

    def test_fromitems_with_items(self):
        result = IndexedDict.fromitems([("a", 1), ("b", 2)])
        assert isinstance(result, IndexedDict)
        assert result["a"] == 1
        assert result["b"] == 2

    def test_fromitems_preserves_order_of_items(self):
        result = IndexedDict.fromitems([("c", 3), ("a", 1), ("b", 2)])
        assert list(result.keys()) == ["c", "a", "b"]

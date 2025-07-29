import pytest
from indexed_dict import IndexedDict


def test_update_with_dict():
    d = IndexedDict({"a": 1, "b": 2})
    d.update({"b": 20, "c": 3})
    assert d["a"] == 1
    assert d["b"] == 20
    assert d["c"] == 3


def test_update_with_items():
    d = IndexedDict({"a": 1, "b": 2})
    d.update([("b", 20), ("c", 3)])
    assert d["a"] == 1
    assert d["b"] == 20
    assert d["c"] == 3


def test_update_with_kwargs():
    d = IndexedDict({"a": 1, "b": 2})
    d.update(b=20, c=3)
    assert d["a"] == 1
    assert d["b"] == 20
    assert d["c"] == 3


def test_update_with_dict_and_kwargs():
    d = IndexedDict({"a": 1, "b": 2})
    d.update({"b": 20}, c=3, d=4)
    assert d["a"] == 1
    assert d["b"] == 20
    assert d["c"] == 3
    assert d["d"] == 4


def test_update_adds_new_keys_at_end():
    d = IndexedDict({"a": 1, "b": 2})
    d.update({"c": 3, "d": 4})
    assert list(d.keys()) == ["a", "b", "c", "d"]


def test_update_with_empty_dict():
    d = IndexedDict({"a": 1, "b": 2})
    d.update({})
    assert d["a"] == 1
    assert d["b"] == 2


def test_update_raises_type_error_for_invalid_arg():
    d = IndexedDict()
    with pytest.raises(TypeError):
        d.update(42)


def test_update_raises_type_error_for_multiple_positional_args():
    d = IndexedDict()
    with pytest.raises(TypeError):
        d.update({}, {})

import pytest
from indexed_dict import IndexedDict


def test_bool_empty_is_false():
    assert not bool(IndexedDict())


def test_bool_non_empty_is_true():
    assert bool(IndexedDict({"a": 1}))

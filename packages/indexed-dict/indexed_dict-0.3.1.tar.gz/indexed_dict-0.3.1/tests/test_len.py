import pytest
from indexed_dict import IndexedDict


def test_len_returns_correct_count():
    assert len(IndexedDict()) == 0
    assert len(IndexedDict({"a": 1})) == 1
    assert len(IndexedDict({"a": 1, "b": 2, "c": 3})) == 3

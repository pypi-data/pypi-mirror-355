import pytest
from indexed_dict import IndexedDict


def test_str_shows_contents():
    d = IndexedDict({"a": 1, "b": 2})
    s = str(d)
    assert s.startswith("{")
    assert s.endswith("}")
    assert "'a': 1" in s
    assert "'b': 2" in s

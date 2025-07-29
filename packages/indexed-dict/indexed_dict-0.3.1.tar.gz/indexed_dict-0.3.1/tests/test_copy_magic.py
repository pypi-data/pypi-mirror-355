import copy
import pytest
from indexed_dict import IndexedDict


def test_copy_magic_method():
    """Test the __copy__ magic method."""
    d1 = IndexedDict({"a": 1, "b": 2})
    d2 = copy.copy(d1)

    assert d1 is not d2
    assert d1 == d2
    assert list(d1.keys()) == list(d2.keys())

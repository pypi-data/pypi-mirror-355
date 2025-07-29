import pytest

from indexed_dict._node import _Node


@pytest.fixture
def test_node():
    return _Node("apple", 0)


def test_node_init(test_node):
    assert test_node.value == "apple"
    assert test_node.index == 0


def test_node_repr(test_node):
    assert repr(test_node) == "_Node(apple, 0)"


def test_node_str(test_node):
    assert str(test_node) == "(apple, 0)"


def test_node_eq_positive(test_node):
    node2 = _Node("apple", 0)
    assert test_node == node2


def test_node_eq_negative(test_node):
    node2 = _Node("banana", 0)
    node3 = _Node("apple", 1)

    assert test_node != node2
    assert test_node != node3
    assert test_node != "not a test_node"

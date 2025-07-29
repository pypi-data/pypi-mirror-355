"""Internal node implementation for IndexedDict."""

from indexed_dict._types import Generic, V


class _Node(Generic[V]):
    """Internal node to store value and index information."""

    __slots__ = ("value", "index")

    def __init__(self, value: V, index: int) -> None:
        self.value = value
        self.index = index

    def __repr__(self) -> str:
        return f"_Node({self.value}, {self.index})"

    def __str__(self) -> str:
        return f"({self.value}, {self.index})"

    def __eq__(self, other) -> bool:
        if not isinstance(other, _Node):
            return False
        return self.value == other.value and self.index == other.index

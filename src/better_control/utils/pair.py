from typing import Generic, TypeVar

T = TypeVar('T')
U = TypeVar('U')


class Pair(Generic[T, U]):
    def __init__(self, first: T, second: U) -> None:
        self.first: T = first
        self.second: U = second

    def __repr__(self) -> str:
        return f"Pair({self.first}, {self.second})"

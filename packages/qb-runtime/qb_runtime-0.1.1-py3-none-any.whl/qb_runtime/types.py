from dataclasses import dataclass
from typing import Iterable, Callable, Iterator
from warnings import warn


class Some[T]:
    def __init__(self, value: T):
        self.value = value

    def unwrap(self) -> T:
        return self.value


type maybe = Some | None
type either = Some | Exception


class collection[T]:
    """A lazy evaluated collection, that behaves like a list, but immutable with some neat additional methods."""

    def __init__(self, *args: T):
        self.args = args

    def for_each(self, func: Callable[[T], None]) -> None:
        if len(self) == 0:
            return

        func(self[0])
        collection(*self[1:]).for_each(func)

    def map(self, func: Callable[[T], T]) -> 'collection[T]':
        if len(self) == 0:
            return self

        return collection(func(self[0]), *collection(*self[1:]).map(func))

    def filter(self, func: Callable[[T], bool]) -> 'collection[T]':
        if len(self) == 0:
            return self

        if func(self[0]):
            return collection(self[0], *collection(*self[1:]).filter(func))

        else:
            return collection(*collection(*self[1:]).filter(func))
        
    def head(self) -> T:
        return self[0]
    
    def tail(self) -> 'collection[T]':
        return collection(*self[1:])

    @staticmethod
    def of(iterable: Iterable[T]):
        if hasattr(iterable, "__len__") and iterable.__len__() == float("inf"):
            warn("Passing an infinite range to collection.of will result in an infinite loop.")

        return collection(*iterable)

    def __iter__(self) -> Iterator[T]:
        return iter(self.args)

    def __getitem__(self, key) -> T:
        return self.args[key]

    def __len__(self) -> int:
        return len(self.args)

    def __repr__(self) -> str:
        return f"collection{self.args}"

    def __str__(self) -> str:
        return f"{self.args}"

    def __contains__(self, item: T) -> bool:
        return item in self.args

    def __eq__(self, other) -> bool:
        return self.args == other.args

    def __ne__(self, other) -> bool:
        return self.args != other.args

    def __add__(self, other: 'collection[T]') -> 'collection[T]':
        return collection(*self.args, *other.args)


@dataclass()
class infinite_range:
    """Returns an object that can be used similar to a normal range object, but with no end."""

    start: int = 0
    step: int = 1

    def __iter__(self):
        return self

    def __next__(self):
        self.start += self.step
        return self.start - self.step

    def __getitem__(self, key):
        if isinstance(key, slice):
            start = key.start if key.start else self.start
            stop = key.stop if key.stop else float("inf")
            step = key.step if key.step else self.step

            return [self.start + i * self.step for i in range(start, stop, step)]
        else:
            return self.start + key * self.step

    def __len__(self):
        return float("inf")

    def __repr__(self):
        return f"infinite_range(start={self.start}, step={self.step})"

    def __str__(self):
        return f"range({self.start}, inf)"

    def __contains__(self, item):
        return (item - self.start) % self.step == 0

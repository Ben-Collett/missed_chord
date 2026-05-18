from collections import Counter


class MyFrozenDict(dict):
    """An immutable, hashable dictionary."""

    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        # Freeze the hash immediately for immutability
        self._hash = None

    def __setitem__(self, key, value):
        raise TypeError(f"{self.__class__.__name__} is immutable")

    def __delitem__(self, key):
        raise TypeError(f"{self.__class__.__name__} is immutable")

    def clear(self):
        raise TypeError(f"{self.__class__.__name__} is immutable")

    def pop(self, *args, **kwargs):
        raise TypeError(f"{self.__class__.__name__} is immutable")

    def popitem(self):
        raise TypeError(f"{self.__class__.__name__} is immutable")

    def setdefault(self, *args, **kwargs):
        raise TypeError(f"{self.__class__.__name__} is immutable")

    def update(self, *args, **kwargs):
        raise TypeError(f"{self.__class__.__name__} is immutable")

    def __hash__(self):
        if self._hash is None:
            # Use a frozenset of items for hash consistency
            self._hash = hash(frozenset(self.items()))
        return self._hash

    def __repr__(self):
        return f"{self.__class__.__name__}({super().__repr__()})"

    @classmethod
    def from_string(cls, s: str):
        """
        Create a FrozenDict representing the frequency map of characters in a string.
        """
        return cls(Counter(s))

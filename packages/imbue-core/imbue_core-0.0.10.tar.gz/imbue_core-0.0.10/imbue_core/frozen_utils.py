from abc import ABC
from abc import abstractmethod
from copy import deepcopy
from functools import cached_property
from typing import Any
from typing import Dict
from typing import FrozenSet
from typing import Iterable
from typing import List
from typing import Mapping
from typing import NoReturn
from typing import Protocol
from typing import Sequence
from typing import Set
from typing import Tuple
from typing import TypeAlias
from typing import TypeVar
from typing import Union
from typing import cast


class _SupportsLessThan(Protocol):
    def __lt__(self, __other: Any) -> bool:
        ...


T = TypeVar("T")
TV = TypeVar("TV")
TK = TypeVar("TK", bound=_SupportsLessThan)


class FrozenMapping(Mapping[T, TV], ABC):
    @abstractmethod
    def __hash__(self) -> int:
        ...


class FrozenDict(Dict[T, TV], FrozenMapping[T, TV]):
    def _key(self) -> FrozenSet[Tuple[T, TV]]:
        return frozenset(self.items())

    @cached_property
    def _hash(self) -> int:
        # bawr said it should be fine
        return hash(self._key())

    def __hash__(self) -> int:  # type: ignore
        return self._hash

    def _mutation_error(self, method: str) -> RuntimeError:
        return RuntimeError(f"Cannot call mutation method {method} on _FrozenDict {self}")

    def __setitem__(self, __name: T, __value: TV) -> NoReturn:
        raise self._mutation_error("__setitem__")

    def __delitem__(self, __name: T) -> NoReturn:
        raise self._mutation_error("__delitem__")

    def update(self, __m: Mapping[T, TV]) -> NoReturn:  # type: ignore
        raise self._mutation_error("update")

    def setdefault(self, __name: T, __value: TV) -> NoReturn:
        raise self._mutation_error("setdefault")

    def pop(self, __name: T, __default: TV) -> NoReturn:  # type: ignore
        raise self._mutation_error("pop")

    def popitem(self) -> NoReturn:
        raise self._mutation_error("popitem")

    def clear(self) -> NoReturn:
        raise self._mutation_error("clear")

    def __repr__(self) -> str:
        return f"_FrozenDict({super().__repr__()})"

    def __copy__(self) -> "FrozenDict":
        return type(self)(self)

    def __deepcopy__(self, memo: Dict[int, Any]) -> "FrozenDict":
        memo[id(self)] = self
        copied_items = ((deepcopy(key, memo), deepcopy(value, memo)) for key, value in self.items())
        return type(self)(copied_items)

    def __reduce__(self) -> Tuple[Any, ...]:
        return (FrozenDict, (dict(self),))


def empty_mapping() -> FrozenDict[Any, Any]:
    return FrozenDict()


def deep_freeze_mapping(mapping: Mapping[T, TV]) -> FrozenDict[T, Any]:
    return FrozenDict({key: cast(TV, _deep_freeze_any(value)) for key, value in mapping.items()})


def _freeze_iterable_values(iterable: Iterable[T]) -> Iterable[Any]:
    return (cast(T, _deep_freeze_any(value)) for value in iterable)


def deep_freeze_set(input_set: Union[Set[T], FrozenSet[T]]) -> FrozenSet[Any]:
    return frozenset(_freeze_iterable_values(input_set))


def _deep_freeze_any(input_object: object) -> object:
    if isinstance(input_object, Mapping):
        return deep_freeze_mapping(input_object)

    if isinstance(input_object, (set, frozenset)):
        return deep_freeze_set(input_object)

    if (
        isinstance(input_object, Iterable)
        and not isinstance(input_object, str)
        and not isinstance(input_object, bytes)
    ):
        return tuple(_freeze_iterable_values(input_object))

    return input_object


def deep_freeze_sequence(sequence: Sequence[T]) -> Tuple[Any, ...]:
    return tuple(_freeze_iterable_values(sequence))


# Recursive type alias that captures the possible types of JSON objects (e.g. from json.loads).
JSON: TypeAlias = Union[str, int, bool, float, None, Dict[str, "JSON"], List["JSON"]]


# Immutable version of JSON.
FrozenJSON: TypeAlias = Union[str, int, bool, float, None, FrozenDict[str, "FrozenJSON"], Tuple["FrozenJSON", ...]]


def deep_freeze_json(json: JSON) -> FrozenJSON:
    if isinstance(json, dict):
        return FrozenDict({k: deep_freeze_json(v) for k, v in json.items()})
    elif isinstance(json, list):
        return tuple(deep_freeze_json(v) for v in json)
    else:
        return json

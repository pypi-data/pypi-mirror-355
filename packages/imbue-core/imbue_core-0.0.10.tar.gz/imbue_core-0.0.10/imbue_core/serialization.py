import builtins
import datetime
import hashlib
import inspect
import json
import traceback
from enum import Enum
from functools import cached_property
from functools import lru_cache
from importlib import import_module
from importlib.metadata import version
from pathlib import PosixPath
from types import TracebackType
from typing import Any
from typing import Callable
from typing import Dict
from typing import Iterable
from typing import List
from typing import Mapping
from typing import Optional
from typing import Tuple
from typing import Type
from typing import TypeVar
from typing import Union
from typing import cast
from uuid import UUID

from loguru import logger
from typing_extensions import TypeAliasType
from yasoo import Deserializer
from yasoo import Serializer
from yasoo.constants import ENUM_VALUE_KEY
from yasoo.objects import DictWithSerializedKeys
from yasoo.serialization import _convert_to_json_serializable
from yasoo.utils import get_fields
from yasoo.utils import is_obj_supported_primitive
from yasoo.utils import normalize_type
from yasoo.utils import resolve_types

from imbue_core.async_monkey_patches import EXCEPTION_LOGGED_FLAG
from imbue_core.fixed_traceback import FixedTraceback
from imbue_core.frozen_utils import FrozenDict
from imbue_core.frozen_utils import FrozenMapping
from imbue_core.pydantic_serialization import SerializableModel
from imbue_core.serialization_types import Serializable

assert (
    version("yasoo") == "0.12.6"
), "This code was written for yasoo 0.12.6 and requires inheriting / monkeypatching the deserializer, so you probably don't want to use any other version without fixing TupleDeserializer"

T = TypeVar("T")


class TupleDeserializer(Deserializer):
    def _deserialize(
        self,
        data: Optional[Union[bool, int, float, str, List[Any], Dict[str, Any]]],
        obj_type: Optional[Type[T]],
        type_key: Optional[str],
        allow_extra_fields: bool,
        external_globals: Dict[str, Any],
        ignore_custom_deserializer: bool = False,
    ) -> object:
        all_globals = dict(globals())
        all_globals.update(external_globals)
        if is_obj_supported_primitive(data):
            return data
        if isinstance(data, list):
            list_types = self._get_list_types(obj_type, data)
            return tuple([self._deserialize(d, t, type_key, allow_extra_fields, all_globals) for t, d in list_types])

        assert isinstance(data, dict), f"Expected a dict, but got {type(data)}"

        # load wrapped primitives
        if type_key is not None:
            type_data = data.get(type_key, None)

            if type_data is not None and type_data.startswith("builtins.") and type_data != "builtins.dict":
                return data["value"]

        # TODO: @josh and @bryden to revisit this, we need to potentially handle `builtins.dict`
        # if type_key is not None:
        #     type_data = data.get(type_key, None)
        #
        #     # TODO (49780118-61e5-446b-b44b-cabb3ffc0ba2): serialization currently breaks with builtin.dicts and dicts with non-string keys
        #     if type_data == "builtins.dict":
        #         raise NotImplementedError(
        #             "Only `FrozenMapping` is supported for dict serialization/deserialization, call `freeze_mapping` on your dict before serializing"
        #         )
        #     if type_data is not None and type_data.startswith("builtins.") and type_data != "builtins.dict":
        #         return data["value"]

        # TODO: remove this hack. Many of our sqlite files (search s3_sqlite_path) have FrozenDicts
        if isinstance(type_key, str) and data.get(type_key, None) == "flax.core.frozen_dict.FrozenDict":
            data[type_key] = "imbue_core.frozen_utils.FrozenMapping"

        obj_type = self._get_object_type(obj_type, data, type_key, all_globals)
        if type_key in data:
            data.pop(type_key)
        real_type, generic_args = normalize_type(obj_type, all_globals)
        if external_globals and isinstance(real_type, type):
            bases = {real_type}
            while bases:
                all_globals.update((b.__name__, b) for b in bases)
                bases = {ancestor for b in bases for ancestor in b.__bases__}

        if not ignore_custom_deserializer:
            deserialization_method = self._custom_deserializers.get(
                obj_type, self._custom_deserializers.get(real_type)
            )
            if deserialization_method:
                return deserialization_method(data)
            for base_class, method in self._inheritance_deserializers.items():
                if issubclass(real_type, base_class):
                    return method(data, real_type)

        key_type = None
        try:
            fields = {f.name: f for f in get_fields(obj_type)}
        except TypeError:
            if obj_type is FixedTraceback:
                return FixedTraceback.from_dict(data["value"])
            if issubclass(real_type, Enum):
                value = data[ENUM_VALUE_KEY]
                if isinstance(value, str):
                    try:
                        return real_type[value]
                    except KeyError:
                        for e in real_type:
                            if e.name.lower() == value.lower():
                                return e
                return real_type(value)
            # TODO (49780118-61e5-446b-b44b-cabb3ffc0ba2): serialization currently breaks with builtin.dicts and dicts with non-string keys
            #   if you have weird keys in your dict this branch won't be hit and your object won't be properly deserialized
            elif issubclass(real_type, Mapping):
                key_type = generic_args[0] if generic_args else None
                if self._is_mapping_dict_with_serialized_keys(key_type, data):
                    obj_type = DictWithSerializedKeys
                    fields = {f.name: f for f in get_fields(obj_type)}
                    value_type = generic_args[1] if generic_args else Any
                    fields["data"].field_type = Dict[str, value_type]  # type: ignore
                else:
                    return self._load_mapping(
                        data,
                        real_type,
                        generic_args,
                        type_key,
                        allow_extra_fields,
                        all_globals,
                    )
            elif issubclass(real_type, Iterable):
                # If we got here it means data is not a list, so obj_type came from the data itself and is safe to use
                return self._load_iterable(data, obj_type, type_key, allow_extra_fields, all_globals)
            elif real_type != obj_type:
                return self._deserialize(data, real_type, type_key, allow_extra_fields, external_globals)
            else:
                raise

        self._check_for_missing_fields(data, fields, obj_type)
        self._check_for_extraneous_fields(data, fields, obj_type, allow_extra_fields)
        self._load_inner_fields(data, fields, type_key, allow_extra_fields, all_globals)
        if obj_type is DictWithSerializedKeys:
            return self._load_dict_with_serialized_keys(
                obj_type(**data), key_type, type_key, allow_extra_fields, all_globals
            )
        kwargs = {k: v for k, v in data.items() if fields[k].init}
        assert obj_type is not None
        result = obj_type(**kwargs)
        for k, v in data.items():
            if k not in kwargs:
                setattr(result, k, v)
        return result


# TODO: probably a good idea to ensure that all dicts are frozen as well...
class FrozenSerializer(Serializer):
    def _serialize_iterable(
        self,
        obj: Iterable[object],
        type_key: Any,
        fully_qualified_types: Any,
        preserve_iterable_types: Any,
        stringify_dict_keys: Any,
    ) -> List[object]:
        if isinstance(obj, list):
            if self._allow_unsafe_list_serialization:
                logger.info(f"Converting list to tuple for serialization: {obj}")
                obj = tuple(obj)
            else:
                raise Exception(
                    f"Lists are not allowed for serialization. Use tuples instead. Current iterable: {obj}"
                )
        assert isinstance(
            obj, (tuple, frozenset, bytes)
        ), f"All iterables should be tuples or frozenset. Received {obj}"
        return cast(
            List[object],
            tuple(
                self._serialize(
                    item,
                    type_key,
                    fully_qualified_types,
                    preserve_iterable_types,
                    stringify_dict_keys,
                )
                for item in obj
            ),
        )

    # overriding this method just to get some better error messages out--previously it would just "type error" and
    # moan about things like int64 not being serializable, which is fine, but it is nicer if the key is included
    def serialize(
        self,
        obj: Any,
        type_key: Optional[str] = "__type",
        fully_qualified_types: bool = True,
        preserve_iterable_types: bool = False,
        stringify_dict_keys: bool = True,
        globals: Optional[Dict[str, Any]] = None,
    ) -> Optional[Union[bool, int, float, str, list, Dict[str, Any]]]:
        try:
            if is_obj_supported_primitive(obj):
                return obj  # type: ignore

            if globals:
                self._custom_serializers = resolve_types(self._custom_serializers, globals)  # type: ignore

            result = self._serialize(
                obj,
                type_key,
                fully_qualified_types,
                preserve_iterable_types,
                stringify_dict_keys,
                inner=False,
            )
            try:
                result = _convert_to_json_serializable(result)
            except TypeError:
                _convert_to_json_serializable_with_better_errors(result)
                assert False, "previous method should have raised..."
            return result  # type: ignore
        except Exception:
            if self._force_serialization:
                return repr(obj)
            else:
                raise

    @staticmethod
    def _get_type_data(obj: Any, fully_qualified_types: bool) -> str:
        return type_to_string(type(obj), fully_qualified_types)  # type: ignore


JsonTypeAlias = TypeAliasType(
    "JsonTypeAlias",
    "Union[dict[str, JsonTypeAlias], list[JsonTypeAlias], str, int, float, bool, None]",
)


class SerializedException(SerializableModel):
    """A serializable dataclass that represents an exception"""

    exception: str
    args: "Tuple[SerializedException | JsonTypeAlias, ...]"
    traceback_dict: JsonTypeAlias
    was_logged_by_log_exception: bool = False

    @classmethod
    def build(cls, exception: BaseException, traceback: Optional[TracebackType] = None) -> "SerializedException":
        if traceback is None:
            traceback = exception.__traceback__
            assert traceback is not None, " ".join(
                (
                    f"No traceback deriveable or as a concrete argument!",
                    f"You probably want to convert_to_serialized_exception in your except clause: {exception=}",
                )
            )
        return SerializedException(
            exception=get_fully_qualified_name_for_error(exception),
            args=tuple(_convert_serialized_exception_args(x, traceback) for x in exception.args),
            traceback_dict=FixedTraceback.from_tb(traceback).as_dict(),
            was_logged_by_log_exception=getattr(exception, EXCEPTION_LOGGED_FLAG, False),
        )

    @cached_property
    def traceback(self) -> Optional[FixedTraceback]:
        if self.traceback_dict is None:
            return None
        return FixedTraceback.from_dict(self.traceback_dict)

    @cached_property
    def exception_module(self) -> str:
        if "." in self.exception:
            return self.exception.rsplit(".", maxsplit=1)[0]
        return ""

    @cached_property
    def exception_type(self) -> str:
        return self.exception.rsplit(".", maxsplit=1)[-1]

    @cached_property
    def exception_class(self) -> Type[BaseException]:
        if self.exception_module:
            return cast(Type[BaseException], getattr(import_module(self.exception_module), self.exception_type, None))
        else:
            return cast(Type[BaseException], getattr(builtins, self.exception_type, None))

    def construct_instance(self) -> BaseException:
        exception = self.exception_class(*cast(Tuple[Serializable, ...], self.args))

        try:
            setattr(exception, EXCEPTION_LOGGED_FLAG, True)
        except AttributeError:
            # We could not set the flag correctly
            pass

        return exception

    def as_formatted_traceback(self) -> str:
        if self.traceback is None:
            traceback_str = ""
        else:
            traceback_str = "".join(traceback.format_tb(self.traceback))
        return f"Traceback (most recent call last):\n{traceback_str}\n{self.exception}: {self.args}"


def _convert_serialized_exception_args(
    error: Serializable, traceback: Optional[TracebackType] = None
) -> JsonTypeAlias:
    if isinstance(error, BaseException):
        return SerializedException.build(error, traceback=traceback)
    elif isinstance(error, (list, tuple)):
        return tuple(_convert_serialized_exception_args(x, traceback) for x in error)
    return error


def get_fully_qualified_name_for_error(e: BaseException) -> str:
    if e.__class__.__module__ == "builtins":
        return e.__class__.__name__
    return f"{e.__class__.__module__}.{e.__class__.__name__}"


# note that the t: Any annotation is because it wants to be Hashable, but types dont conform to that. Doesn't matter though, we're deleting all of this code soon anyway...
@lru_cache(None)
def type_to_string(t: Any, fully_qualified: bool) -> str:
    name = str(t.__name__)
    if fully_qualified:
        full_name = ".".join((t.__module__, name))
        # TODO: a sort of gross hack... not 100% sure how to do a better job with imports given that we need to make these temporary test files
        #  once we've moved to separate containers, we could move away from this I suppose, since we could edit the files without causing problems with concurrency
        if ".imbuetest_" in full_name:
            return name
        else:
            return full_name
    else:
        return name


def _convert_to_json_serializable_with_better_errors(
    obj: Any, path: str = ""
) -> Union[int, float, str, list, dict, None]:
    if is_obj_supported_primitive(obj):
        return obj  # type: ignore
    if isinstance(obj, Mapping):
        return {
            key: _convert_to_json_serializable_with_better_errors(value, f"{path}.{key}") for key, value in obj.items()
        }
    if isinstance(obj, Iterable):
        return [_convert_to_json_serializable_with_better_errors(item, f"{path}[{i}]") for i, item in enumerate(obj)]
    raise TypeError(f'Found object of type "{type(obj).__name__}" at {path} which cannot be serialized')


SERIALIZER = FrozenSerializer()
SERIALIZER._allow_unsafe_list_serialization = False
SERIALIZER._force_serialization = False
FORCING_SERIALIZER = FrozenSerializer()
FORCING_SERIALIZER._allow_unsafe_list_serialization = True
FORCING_SERIALIZER._force_serialization = True
DESERIALIZER = TupleDeserializer()

# note: you cannot change this without changing other calls to yasoo, this is its default
TYPE_KEY = "__type"


class SerializationError(Exception):
    pass


# TODO: I don't think this ever actually runs
@SERIALIZER.register()
@FORCING_SERIALIZER.register()
def serialize_frozen_mapping(data: FrozenMapping) -> Dict:
    value = SERIALIZER.serialize(data)
    value[TYPE_KEY] = type_to_string(type(data), fully_qualified=True)  # type: ignore
    return cast(Dict[Any, Any], value)


@DESERIALIZER.register()
def deserialize_frozen_mapping(data: Dict) -> FrozenMapping:
    return FrozenDict(DESERIALIZER.deserialize(data, dict))


@SERIALIZER.register()
@FORCING_SERIALIZER.register()
def serialize_frozen_set(data: frozenset) -> Dict:
    value = SERIALIZER.serialize(tuple(data))
    return {"value": value}


@DESERIALIZER.register()
def deserialize_frozen_set(data: Dict) -> frozenset:
    return frozenset(DESERIALIZER.deserialize(data["value"], tuple))


@SERIALIZER.register()
@FORCING_SERIALIZER.register()
def serialize_uuid(data: UUID) -> Dict:
    return {"value": data.hex}


@DESERIALIZER.register()
def deserialize_uuid(data: Dict) -> UUID:
    return UUID(data["value"])


@SERIALIZER.register()
@FORCING_SERIALIZER.register()
def serialize_traceback(data: FixedTraceback) -> Dict:
    return {"value": data.to_dict()}


@DESERIALIZER.register()
def deserialize_traceback(data: Dict) -> FixedTraceback:
    return FixedTraceback.from_dict(data["value"])


@SERIALIZER.register()
@FORCING_SERIALIZER.register()
def serialize_posix_path(data: PosixPath) -> Dict:
    return {"value": str(data)}


@DESERIALIZER.register()
def deserialize_posix_path(data: Dict) -> PosixPath:
    return PosixPath(data["value"])


@SERIALIZER.register()
@FORCING_SERIALIZER.register()
def serialize_datetime(data: datetime.datetime) -> Dict:
    return {
        "time": data.astimezone(datetime.timezone.utc).timestamp(),
        "tzaware": data.tzinfo is not None,
        "__type": "datetime.datetime",
    }


@DESERIALIZER.register()
def deserialize_datetime(data: Dict) -> datetime.datetime:
    return datetime.datetime.fromtimestamp(data["time"], datetime.timezone.utc if data.get("tzaware", None) else None)


def serialize_to_dict(obj: Any) -> Dict[str, Any]:
    return cast(Dict[str, Any], SERIALIZER.serialize(obj))


def force_serialize_to_dict(obj: Any) -> Mapping[str, Any]:
    """Forces primitives to become dicts as well by wrapping with a type"""
    if obj is None:
        return {}
    if is_obj_supported_primitive(obj):
        return {"value": obj, TYPE_KEY: "builtins." + type(obj).__name__}
    return cast(Mapping[str, Any], SERIALIZER.serialize(obj))


def serialize_to_json(obj: Any, indent: Optional[int] = None, sort_keys: bool = False) -> str:
    try:
        return json.dumps(SERIALIZER.serialize(obj), indent=indent, sort_keys=sort_keys)
    except Exception as e:
        raise SerializationError(str(e)) from e


def force_serialize_to_json(obj: Any, indent: Optional[int] = None, sort_keys: bool = False) -> str:
    return json.dumps(FORCING_SERIALIZER.serialize(obj), indent=indent, sort_keys=sort_keys)


def deserialize_from_json(data: str) -> Any:
    try:
        return DESERIALIZER.deserialize(json.loads(data))
    except Exception as e:
        raise SerializationError(str(e)) from e


def deserialize_from_dict(data: Dict[str, Any]) -> Any:
    try:
        return DESERIALIZER.deserialize(data)
    except Exception as e:
        raise SerializationError(str(e)) from e


def deserialize_from_dict_with_type(data: Dict[str, Any], obj_type: Type[T]) -> T:
    try:
        result = DESERIALIZER.deserialize(data, obj_type=obj_type)
        assert isinstance(result, obj_type), f"Expected an object of type {obj_type}, but got {result}"
        return result
    except Exception as e:
        raise SerializationError(str(e)) from e


def deserialize_from_json_with_type(data: Union[str, bytes, bytearray], obj_type: Type[T]) -> T:
    try:
        return deserialize_from_dict_with_type(json.loads(data), obj_type=obj_type)
    except Exception as e:
        raise SerializationError(str(e)) from e


def calculate_object_content_hash(obj: Any, keys_to_ignore: Iterable[str]) -> str:
    hash = hashlib.md5()
    hash.update(
        serialize_to_json(
            {
                k: getattr(obj, k) if k != "__type" else obj.__class__.__name__
                for k in serialize_to_dict(obj).keys()
                if k not in keys_to_ignore
            }
        ).encode()
    )
    return hash.hexdigest()


def get_serializable_properties(obj: Any) -> Dict[str, Any]:
    members = inspect.getmembers(type(obj))
    marked_members = [name for name, member in members if is_serializable_property(member)]
    return {name: getattr(obj, name) for name in marked_members}


def is_serializable_property(func: Callable) -> bool:
    return getattr(func, "_imbue_is_serializable_property", False)

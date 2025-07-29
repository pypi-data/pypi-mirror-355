from typing import Annotated
from typing import Dict

from inline_snapshot import snapshot
from typing_extensions import TypeAliasType

from imbue_core.frozen_utils import FrozenDict
from imbue_core.frozen_utils import deep_freeze_mapping
from imbue_core.pydantic_serialization import PydanticFrozenDictAnnotation
from imbue_core.pydantic_serialization import SerializableModel
from imbue_core.pydantic_serialization import model_dump
from imbue_core.pydantic_serialization import model_dump_json
from imbue_core.pydantic_serialization import model_load
from imbue_core.pydantic_serialization import model_load_json


class TestObject(SerializableModel):
    name: str
    language_code: str
    inner_data: Dict[str, str]


def test_simple() -> None:
    obj = TestObject(**dict(name="Filiz", languageCode="tr-TR", innerData={"snake_key": "value", "camelKey": "value"}))
    assert model_dump(obj) == snapshot(
        {
            "name": "Filiz",
            "language_code": "tr-TR",
            "inner_data": {"snake_key": "value", "camelKey": "value"},
        }
    )


def test_to_camel() -> None:
    obj = TestObject(**dict(name="Filiz", languageCode="tr-TR", innerData={"snake_key": "value", "camelKey": "value"}))
    assert model_dump(obj, is_camel_case=True) == snapshot(
        {
            "name": "Filiz",
            "languageCode": "tr-TR",
            "innerData": {"snake_key": "value", "camelKey": "value"},
        }
    )


def test_reversible() -> None:
    obj = TestObject(**dict(name="Filiz", languageCode="tr-TR", innerData={"snake_key": "value", "camelKey": "value"}))
    assert model_load(TestObject, model_dump(obj)) == obj


class Example(SerializableModel):
    mapping: Annotated[FrozenDict[int | float, int | None | tuple[int, ...]], PydanticFrozenDictAnnotation]


def test_arbitrary_frozen_dict() -> None:
    x = deep_freeze_mapping(FrozenDict({0: 0, 0.10: None, 100: [1, 2, 3]}))
    obj = Example(mapping=x, mapping_orig=x)
    assert isinstance(obj.mapping, FrozenDict)
    assert obj.mapping == x
    assert obj.model_dump() == {"mapping": x}
    json = obj.model_dump_json()
    loaded = Example.model_validate_json(json)
    assert isinstance(loaded.mapping, FrozenDict)
    assert loaded.mapping == x


FrozenJSON = TypeAliasType(
    "FrozenJSON",
    "Union[FrozenDict[str, FrozenJSON], list[FrozenJSON], str, int, float, bool, None]",
)


class JsonExample(SerializableModel):
    mapping: Annotated[FrozenJSON, PydanticFrozenDictAnnotation]


def test_frozen_json() -> None:
    obj = JsonExample(
        mapping=FrozenDict(
            {
                "key1": FrozenDict({"key2": FrozenDict({"key3": 1})}),
                "key4": FrozenDict({"key5": FrozenDict({"key6": 2})}),
                "list_key": [1, 2, 4.4, "string", True],
            }
        )
    )
    assert model_load_json(JsonExample, model_dump_json(obj)) == obj


def test_evolve() -> None:
    obj = TestObject(
        name="Filiz",
        language_code="tr-TR",
        inner_data={"snake_key": "value", "camelKey": "value"},
    )
    new_obj = obj.evolve(obj.ref().name, "thing")
    assert new_obj.name == "thing"
    assert obj.name == "Filiz"

from typing import TYPE_CHECKING, Any, Optional, Union

from pydantic import BaseModel
from pydantic_core import PydanticUndefined, to_jsonable_python

if TYPE_CHECKING:
    from pydantic.typing import AbstractSetIntStr, MappingIntStrAny

JsonSerialisableData = Union[
    str, int, float, bool, None, dict[str, "JsonSerialisableData"], list["JsonSerialisableData"]
]


def serialise_model(
    obj: BaseModel,
    *,
    include: Optional[Union["AbstractSetIntStr", "MappingIntStrAny"]] = None,
    exclude: Optional[Union["AbstractSetIntStr", "MappingIntStrAny"]] = None,
    by_alias: bool = False,
    exclude_unset: bool = False,
    exclude_defaults: bool = False,
    exclude_none: bool = False,
) -> JsonSerialisableData:
    data = obj.model_dump(
        include=include,
        exclude=exclude,
        by_alias=by_alias,
        exclude_unset=exclude_unset,
        exclude_defaults=exclude_defaults,
        exclude_none=exclude_none,
    )
    return serialise(data=data)


def serialise(data: Any) -> JsonSerialisableData:  # type: ignore[return]
    match data:
        case dict():
            return {item: serialise(value) for item, value in data.items()}
        case list():
            return [serialise(item) for item in data]
        case str() | int() | float() | bool() | None:
            return data
        case x if x is PydanticUndefined:
            return None
        case _:
            return to_jsonable_python(data)  # type: ignore[no-any-return]

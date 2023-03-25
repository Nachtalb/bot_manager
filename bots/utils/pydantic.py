from typing import TYPE_CHECKING, Any, Optional, Union

from pydantic import BaseModel
from pydantic.json import ENCODERS_BY_TYPE

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
    skip_defaults: Optional[bool] = None,
    exclude_unset: bool = False,
    exclude_defaults: bool = False,
    exclude_none: bool = False,
) -> JsonSerialisableData:
    data = obj.dict(
        include=include,
        exclude=exclude,
        by_alias=by_alias,
        skip_defaults=skip_defaults,
        exclude_unset=exclude_unset,
        exclude_defaults=exclude_defaults,
        exclude_none=exclude_none,
    )
    return serialise(data)


def serialise(data: Any) -> JsonSerialisableData:
    match data:
        case dict():
            return {item: serialise(value) for item, value in data.items()}
        case list():
            return [serialise(item) for item in data]
        case str() | int() | float() | bool() | None:
            return data
        case _:
            for base in data.__class__.__mro__[:-1]:
                try:
                    encoder = ENCODERS_BY_TYPE[base]
                except KeyError:
                    continue
                return encoder(data)

from typing import TYPE_CHECKING, Any, Optional, Union

from pydantic import BaseModel
from pydantic.json import ENCODERS_BY_TYPE

if TYPE_CHECKING:
    from pydantic.typing import AbstractSetIntStr, MappingIntStrAny


def serialised_dict(
    obj: BaseModel,
    *,
    include: Optional[Union["AbstractSetIntStr", "MappingIntStrAny"]] = None,
    exclude: Optional[Union["AbstractSetIntStr", "MappingIntStrAny"]] = None,
    by_alias: bool = False,
    skip_defaults: Optional[bool] = None,
    exclude_unset: bool = False,
    exclude_defaults: bool = False,
    exclude_none: bool = False,
) -> dict[str, Any]:
    data = obj.dict(
        include=include,
        exclude=exclude,
        by_alias=by_alias,
        skip_defaults=skip_defaults,
        exclude_unset=exclude_unset,
        exclude_defaults=exclude_defaults,
        exclude_none=exclude_none,
    )

    for key, value in data.items():
        for base in value.__class__.__mro__[:-1]:
            try:
                encoder = ENCODERS_BY_TYPE[base]
            except KeyError:
                continue
            data[key] = encoder(value)
    return data

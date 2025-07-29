from typing import Type
from fastapi import Depends, Query
from pydantic import BaseModel
from inspect import Signature, Parameter

def as_query(model: Type[BaseModel]):
    def dependency(**kwargs):
        return model(**kwargs)

    parameters = []
    for name, field in model.__fields__.items():
        default = Query(None)
        param = Parameter(
            name,
            Parameter.KEYWORD_ONLY,
            default=default,
            annotation=field.annotation,  # Pydantic v2 中应使用 annotation
        )
        parameters.append(param)

    dependency.__signature__ = Signature(parameters)
    return Depends(dependency)
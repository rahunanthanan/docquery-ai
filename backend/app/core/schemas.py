"""Shared schema base: the API speaks camelCase JSON (like the §9 envelope's
``requestId``), while Python code stays snake_case."""

from pydantic import BaseModel, ConfigDict
from pydantic.alias_generators import to_camel


class CamelModel(BaseModel):
    model_config = ConfigDict(alias_generator=to_camel, populate_by_name=True)

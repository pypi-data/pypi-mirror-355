import warnings

from pydantic import (
    BaseModel, Field, ConfigDict,
    field_validator, model_validator, computed_field,
)
from pydantic.alias_generators import to_snake
from pydantic.json_schema import PydanticJsonSchemaWarning


__all__ = [
    'BaseSchema',
    'Field',
    'CamelBaseSchema',
    'field_validator',
    'model_validator',
    'computed_field',
]


class BaseSchema(BaseModel):

    model_config = ConfigDict(
        use_enum_values         = True,
        extra                   = 'ignore',
    )

    def model_dump(self, **kwargs) -> dict:
        kwargs.setdefault('warnings', False)
        return super().model_dump(**kwargs)


class CamelBaseSchema(BaseSchema):
    '''Base schema for models that use camelCase for field names.
    '''

    def __init__(self, **data):
        # XXX: FastAPI ignores `by_field` values
        data = {to_snake(k): v for k, v in data.items()}
        super().__init__(**data)


warnings.filterwarnings(
    'ignore',
    category=UserWarning,
    message=r'Field name .* shadows an attribute in parent .*',
)

warnings.filterwarnings(
    'ignore',
    category=PydanticJsonSchemaWarning,
    message=r'.* \[non-serializable-default\]',
)

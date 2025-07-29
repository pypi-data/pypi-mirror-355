from scap._core.sql_patch import patch_sqlmodel_table_construct, patch_type_mapping
patch_sqlmodel_table_construct()
patch_type_mapping()

from sqlmodel import (
    SQLModel, Field, Relationship, select,
    ForeignKeyConstraint, PrimaryKeyConstraint, UniqueConstraint,
)
from sqlalchemy.orm import declared_attr
from pydantic.alias_generators import to_snake


__all__ = [
    'BaseSqlModel', 'Field', 'Relationship', 'select',
    'ForeignKeyConstraint', 'PrimaryKeyConstraint', 'UniqueConstraint',
]


class BaseSqlModel(SQLModel):

    @declared_attr  # type: ignore
    def __tablename__(cls) -> str:
        return to_snake(cls.__name__).removeprefix('sql_')

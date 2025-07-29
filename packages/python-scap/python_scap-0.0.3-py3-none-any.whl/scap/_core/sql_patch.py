# mypy: ignore-errors

# fixes https://github.com/fastapi/sqlmodel/issues/293
def patch_sqlmodel_table_construct():

    import sqlmodel._compat

    def sqlmodel_table_construct(*,self_instance, values, _fields_set = None):
        # Copy from Pydantic's BaseModel.construct()
        # Ref: https://github.com/pydantic/pydantic/blob/v2.5.2/pydantic/main.py#L198
        # Modified to not include everything, only the model fields, and to
        # set relationships
        # SQLModel override to get class SQLAlchemy __dict__ attributes and
        # set them back in after creating the object
        # new_obj = cls.__new__(cls)
        cls = type(self_instance)
        old_dict = self_instance.__dict__.copy()
        # End SQLModel override

        fields_values = {}
        defaults = {}  # keeping this separate from `fields_values` helps us compute `_fields_set`
        for name, field in cls.model_fields.items():
            if field.alias and field.alias in values:
                fields_values[name] = values.pop(field.alias)
            elif name in values:
                fields_values[name] = values.pop(name)
            elif not field.is_required():
                defaults[name] = field.get_default(call_default_factory=True)
        if _fields_set is None:
            _fields_set = set(fields_values.keys())
        fields_values.update(defaults)

        _extra = None
        if cls.model_config.get("extra") == "allow":
            _extra = {}
            for k, v in values.items():
                _extra[k] = v
        # SQLModel override, do not include everything, only the model fields
        # else:
        #     fields_values.update(values)
        # End SQLModel override
        # SQLModel override
        # Do not set __dict__, instead use setattr to trigger SQLAlchemy
        # object.__setattr__(new_obj, "__dict__", fields_values)
        # instrumentation
        for key, value in {**old_dict, **fields_values}.items():
            setattr(self_instance, key, value)
        # End SQLModel override
        object.__setattr__(self_instance, "__pydantic_fields_set__", _fields_set)
        if not cls.__pydantic_root_model__:
            object.__setattr__(self_instance, "__pydantic_extra__", _extra)

        if cls.__pydantic_post_init__:
            self_instance.model_post_init(None)
        elif not cls.__pydantic_root_model__:
            # Note: if there are any private attributes, cls.__pydantic_post_init__ would exist
            # Since it doesn't, that means that `__pydantic_private__` should be set to None
            object.__setattr__(self_instance, "__pydantic_private__", None)
        # SQLModel override, set relationships
        # Get and set any relationship objects
        for rel_name, rel_info in self_instance.__sqlmodel_relationships__.items():

            attr = values.get(rel_name)
            if attr is None:
                continue

            # use sqlmodel internal function to get class
            anno = cls.__annotations__[rel_name].__args__[0]
            rel_class_name = sqlmodel._compat.get_relationship_to(
                name=rel_name, rel_info=rel_info, annotation=anno)

            # might be type or string depending on how it was declared
            if isinstance(rel_class_name, type):
                rel_class = rel_class_name
            else:
                rel_class = globals()[rel_class_name]

            # convert attribute(s) with their model's validator
            if isinstance(attr, list):
                items = [rel_class.model_validate(item) for item in attr]
                setattr(self_instance, rel_name, items)
            else:
                item = rel_class.model_validate(attr)
                setattr(self_instance, rel_name, item)

        # End SQLModel override
        return self_instance

    sqlmodel._compat.sqlmodel_table_construct = sqlmodel_table_construct


def patch_type_mapping():

    # XXX: monkey-patch sqlmodel to costumize the pydantic field to
    #   sqlalchemy type mapping
    from pydantic_core import PydanticUndefined
    import sqlmodel.main
    _get_sqlalchemy_type = sqlmodel.main.get_sqlalchemy_type
    import sqlmodel._compat

    import uuid
    from .sql_types import GUID

    def get_sqlalchemy_type(field):

        if hasattr(field, 'sa_type'):
            if field.sa_type is not PydanticUndefined:
                return field.sa_type

        type_ = sqlmodel._compat.get_sa_type_from_field(field)
        # metadata = sqlmodel._compat.get_field_metadata(field)

        if issubclass(type_, uuid.UUID):
            return GUID

        return _get_sqlalchemy_type(field)

    sqlmodel.main.get_sqlalchemy_type = get_sqlalchemy_type

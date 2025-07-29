from datetime import datetime
from uuid import UUID
from copy import copy

import pytest

from scap._core.sql import BaseSqlModel
from scap.sql_models.cpe import SqlCpeItem, SqlCpeDeprecation

from sqlmodel import Session, create_engine, select


@pytest.fixture
def engine():
    engine = create_engine('sqlite:///:memory:', echo=False)
    BaseSqlModel.metadata.create_all(engine)
    return engine


@pytest.fixture
def session(engine):
    with Session(engine) as session:
        yield session


def test_create_item(session, cpe_data, log):
    from scap.schemas.cpe import CpeItem

    for product in cpe_data:
        m = CpeItem.model_validate(copy(product))
        i = SqlCpeItem(**m.model_dump())
        v = SqlCpeItem.model_validate(i)
        session.add(v)

        for d in product.get('deprecatedBy', []):
            m = SqlCpeDeprecation.model_validate({
                'deprecated_by_id': d['cpeNameId'],
                'deprecates_id': i.id,
            })
            session.add(m)

    session.commit()

    stmt = select(SqlCpeItem).where(SqlCpeItem.id == 'AB88534D-D94B-4378-9C5F-4B056BAF6967')
    item = session.exec(stmt).first()

    assert item.id == UUID('AB88534D-D94B-4378-9C5F-4B056BAF6967')
    assert item.name == 'cpe:2.3:o:microsoft:windows_nt:4.0:sp1:terminal_server:*:*:*:*:*'
    assert item.deprecated is True
    assert item.title == 'Microsoft Windows NT Terminal Server 4.0 SP1'
    assert item.created == datetime(2007, 8, 23, 21, 16, 59, 567000)
    assert item.last_modified == datetime(2019, 5, 8, 22, 4, 40, 963000)

    assert len(item.refs) == 1
    assert item.refs[0].ref == 'https://www.microsoft.com/en-us/'

    assert [d.id for d in item.deprecated_by] == [
        UUID('3949c1c7-f13f-47b5-af22-a6ca209113cd'),
        UUID('b2df762f-a615-44a8-b3e0-95cfba6f9a6b'),
    ]
    assert [d.id for d in item.deprecates] == [UUID('c1afe693-cc1c-4113-aec2-03281882a190')]

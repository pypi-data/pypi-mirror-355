from typing import Any, Annotated, Literal
from uuid import UUID

from fastapi import APIRouter, HTTPException, Depends

from scap._core.sql import select
from scap.schemas.cpe import CpeItem, CpeName
from scap.sql_models.cpe import SqlCpeItem
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy.orm import selectinload


cpe_router = APIRouter(prefix='/cpe')


Part = Literal['a', 'h', 'o']


async def get_scap_session() -> Any:
    raise NotImplementedError('You must override this dependency in the app')


@cpe_router.get('/vendors', response_model=dict[str, list[str]])
async def get_unique_vendors(
    session: Annotated[AsyncSession, Depends(get_scap_session)],
    part:    Part | None = None,
):
    stmt = select(SqlCpeItem.vendor).distinct()
    if part is not None:
        stmt = stmt.where(SqlCpeItem.part == part)
    result = await session.execute(stmt)
    return {'data:': sorted(result.scalars().all())}


@cpe_router.get('/vendors/{vendor}/products', response_model=dict[str, list[str]])
async def get_vendor_products(
    vendor:  str,
    session: Annotated[AsyncSession, Depends(get_scap_session)],
    part:    Part | None = None,
):
    stmt = select(SqlCpeItem.product).where(SqlCpeItem.vendor == vendor)
    if part is not None:
        stmt = stmt.where(SqlCpeItem.part == part)

    # TODO: if empty check vendor and raise 404 if vendor doesn't exist
    result = await session.execute(stmt.distinct())
    return {'data:': sorted(result.scalars().all())}


@cpe_router.get('/{id_or_name}', response_model=CpeItem)
async def get_cpe(
    id_or_name: str,
    session:    Annotated[AsyncSession, Depends(get_scap_session)],
) -> CpeItem:

    stmt = select(SqlCpeItem).options(
        selectinload(SqlCpeItem.deprecates),
        selectinload(SqlCpeItem.deprecated_by),
        selectinload(SqlCpeItem.refs),
    )

    try:
        stmt = stmt.where(SqlCpeItem.id == UUID(id_or_name))
    except ValueError:
        try:
            stmt = stmt.where(SqlCpeItem.name == CpeName(id_or_name))
        except TypeError:
            raise HTTPException(400, 'Invalid format. ID must either an UUID or a CPE name.')

    result = await session.execute(stmt)

    if not (item := result.scalar_one_or_none()):
        raise HTTPException(status_code=404, detail='CPE not found')

    return item

from contextlib import asynccontextmanager

from scap.schemas.cpe import CpeItem
from typing import Any
from fastapi import FastAPI, Depends
from sqlalchemy.ext.asyncio import AsyncSession, create_async_engine
from sqlalchemy.orm import sessionmaker
from scap.api.cpe import cpe_router, get_scap_session
from scap.schemas.cpe import CpeName

DATABASE_URL = "sqlite+aiosqlite:///./db2.sqlite"

engine = create_async_engine(DATABASE_URL, echo=False)
AsyncSessionLocal = sessionmaker(
    bind=engine,
    class_=AsyncSession,
    expire_on_commit=False
)

async def get_db():
    async with AsyncSessionLocal() as session:  # Correcto: maneja el ciclo de vida
        yield session


app = FastAPI()
app.dependency_overrides[get_scap_session] = get_db
from fastapi.dependencies.models import Dependant

# 5bd99af033a44f358d886dc02a3bfad6


# app.include_router(cpe_router, dependencies=[Depends(lambda: AsyncSessionLocal())])

app.include_router(cpe_router, tags=['cpe'], dependencies=[Depends(get_db)])


# Sobrescribimos los parámetros `session` para inyectar `get_db()`
for route in app.routes:
    if hasattr(route, 'dependencies'):
        print(route.dependencies)
        print(route.dependant)
        print('ROUTE', route)
        print(dir(route))
    # if hasattr(route, 'dependant'):
    #     for dependency in route.dependant.dependencies:
    #         print('---')
    #         print('PATH', dependency.path)
    #         print('PATH', dependency.name)
    #         print((dir(dependency)))
    #         print('DEPS', dependency.dependencies)
    #         print('ANNO', dependency.__annotations__)
    #         print(dependency.__module__)
    #         dependency.dependencies = [get_db]  # Reemplazamos las dependencias con `get_db()`
    #         # if dependency.name == "session":  # Si el endpoint tiene un parámetro `session`
    #         #     dependency.dependency = get_db  # Lo reemplazamos con `get_db()`



if __name__ == '__main__':
    import asyncio
    import sys
    import re
    # asyncio.run(test())

    import json
    data = CpeItem.model_json_schema(by_alias=False)
    print(json.dumps(data, indent=2))

    from hypercorn.asyncio import serve
    from hypercorn.config import Config
    import asyncio

    config = Config()
    config.bind = ["0.0.0.0:8000"]

    asyncio.run(serve(app, config))

    # name = CpeName("cpe:2.3:h:3com:tippingpoint_ips:-:*:*:*:*:*:*:*")

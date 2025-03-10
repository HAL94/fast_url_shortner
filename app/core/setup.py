from typing import Any, AsyncGenerator, Callable
from contextlib import _AsyncGeneratorContextManager, asynccontextmanager
from fastapi import APIRouter, FastAPI

from app.core.config import AppSettings, PostgresSettings
from app.core.db.database import engine, Base
from app.core.db.models import *

async def create_tables() -> None:
    try:
        async with engine.begin() as conn:
            print("Starting table creation...")
            await conn.run_sync(Base.metadata.create_all)
            print("Tables created successfully")
    except Exception as e:
        print(f"Error creating tables: {e}")


def applifespan_factory(
    settings: AppSettings,
    create_tables_on_start: bool = True
) -> Callable[[FastAPI], _AsyncGeneratorContextManager[Any]]:

    @asynccontextmanager
    async def lifespan(app: FastAPI) -> AsyncGenerator:
        if isinstance(settings, PostgresSettings) and create_tables_on_start:
            await create_tables()
        
        yield
        
        await engine.dispose()
    
    return lifespan
     
def create_application(
    router: APIRouter,
    settings: AppSettings,
    create_tables_on_start: bool = True,
    **kwargs: Any,
) -> FastAPI:   
    lifespan = applifespan_factory(settings, create_tables_on_start=create_tables_on_start)
    
    application = FastAPI(lifespan=lifespan, **kwargs)
    
    application.include_router(router)
    
    return application
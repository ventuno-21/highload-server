from typing import Annotated
from fastapi import FastAPI, Depends, HTTPException
from app.db import get_session
from . import crud, schemas
from .db import engine, get_session
from sqlalchemy.ext.asyncio import AsyncEngine
from contextlib import asynccontextmanager
from sqlalchemy.ext.asyncio import AsyncSession


SessionDep = Annotated[AsyncSession, Depends(get_session)]


@asynccontextmanager
async def lifespan(app: FastAPI):
    print("🚀 Starting up... Testing DB connection")
    try:
        async with engine.begin() as conn:
            await conn.run_sync(lambda x: None)
        print("✅ DB connection OK")
    except Exception as e:
        print("❌ DB connection failed:", e)
        raise e

    yield

    print("🔻 Shutting down... Closing engine")
    await engine.dispose()


app = FastAPI(lifespan=lifespan)


@app.post("/items", response_model=schemas.ItemRead, status_code=201)
async def create_item_endpoint(item: schemas.ItemCreate, db=Depends(get_session)):
    created = await crud.create_item(db, item)
    return created


@app.get("/items", response_model=list[schemas.ItemRead])
async def get_items_endpoint(limit: int = 100, db=Depends(get_session)):
    items = await crud.list_items(db, limit=limit)
    return items

from contextlib import asynccontextmanager
from typing import Annotated, List

from fastapi import Depends, FastAPI, HTTPException
from sqlalchemy.ext.asyncio import AsyncEngine, AsyncSession

from app.db import get_session

from app import crud, db, schemas, tasks
from .cache import get_cache, set_cache
from .db import engine, get_session

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


@app.post("/items", status_code=201)
async def create_item_endpoint(item: schemas.ItemCreate):
    tasks.create_item_task.delay(item.dict())
    return {"message": "Item creation in progress"}


# Without Celery
# @app.post("/items", response_model=schemas.ItemRead, status_code=201)
# async def create_item_endpoint(item: schemas.ItemCreate, db=Depends(get_session)):
#     created = await crud.create_item(db, item)
#     return created


@app.get("/items", response_model=List[schemas.ItemRead])
async def get_items_endpoint(
    limit: int = 100, db: AsyncSession = Depends(db.get_session)
):
    cache_key = f"items:limit={limit}"

    cached = await get_cache(cache_key)
    if cached:
        return cached
    else:
        items = await crud.list_items(db, limit=limit)

        # NOTE: Pydantic models → dict
        # Input:  a list of ORM objects (e.g., SQLAlchemy model instances)
        # Output: a list of plain dicts ready for JSON serialization
        #
        # Explanation:
        # `from_orm()` converts each ORM model instance into a Pydantic schema object.
        # `.dict()` serializes that schema into a clean Python dictionary.
        # This ensures the response contains JSON-safe, validated data rather than raw ORM objects.
        # Example:
        # ORM input:
        #   items = [
        #       Item(id=1, name="Book", price=12.5),
        #       Item(id=2, name="Pen",  price=2.0)
        #   ]
        #
        # After conversion:
        #   data = [
        #       {"id": 1, "name": "Book", "price": 12.5},
        #       {"id": 2, "name": "Pen",  "price": 2.0}
        #   ]
        data = [schemas.ItemRead.model_validate(i).model_dump() for i in items]

        await set_cache(cache_key, data, ttl=60)
        return data


# Without caching
# @app.get("/items", response_model=list[schemas.ItemRead])
# async def get_items_endpoint(limit: int = 100, db=Depends(get_session)):
#     items = await crud.list_items(db, limit=limit)
#     return items

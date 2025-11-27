import asyncio

from asgiref.sync import async_to_sync
from celery import Celery
from sqlalchemy.ext.asyncio import AsyncSession, create_async_engine
from sqlalchemy.orm import sessionmaker

from .cache import get_redis
from .crud import create_item
from .models import Item
from .schemas import ItemCreate

celery_app = Celery(
    "worker",
    broker="pyamqp://guest:guest@rabbitmq:5672//",
)

DATABASE_URL = "postgresql+asyncpg://postgres:postgres@db:5432/db"


@celery_app.task
def create_item_task(item_data: dict):
    """
    Celery task to create an Item in the database asynchronously
    and invalidate related cache keys in Redis.

    Input:
      item_data: dict → dictionary containing Item fields, e.g.,
                 {"name": "Pen", "description": "Blue pen"}

    Output:
      None → item is created in the database and cache is cleared

    Notes:
      - This function is a synchronous Celery task but internally runs
        asynchronous code for database and Redis operations.
      - `asyncio.run(_create())` is used to execute async code in a sync context.
      - Cache invalidation deletes all keys matching "items:*" to ensure
        GET endpoints return fresh data.
      - Multiple Celery workers can run this task concurrently,
        allowing parallel processing of multiple POST requests.

    Example:
      # Trigger task from FastAPI endpoint
      create_item_task.delay({"name": "Notebook", "description": "A5 notebook"})
    """
    engine = create_async_engine(DATABASE_URL, future=True)
    AsyncSessionLocal = sessionmaker(
        engine, class_=AsyncSession, expire_on_commit=False
    )

    async def _create():
        # Async DB session
        async with AsyncSessionLocal() as session:
            # Convert dict to Pydantic model
            item = ItemCreate(**item_data)
            # Save item in DB
            await create_item(session, item)

            # Clear all cached item lists in Redis which the keys started with "items:"
            redis = await get_redis()
            keys = await redis.keys("items:*")
            if keys:
                await redis.delete(*keys)

            await engine.dispose()

    # Run the async function inside a synchronous Celery task
    # asyncio.run(_create())
    """
    asyncio.run() creates a new event loop, which is unsafe inside Celery workers because an event loop may already be running.
    async_to_sync() is designed specifically for safely executing async functions inside synchronous environments (Celery, Django, WSGI apps).

    Detailed Explanation
    Celery workers often execute tasks in environments where:
    An event loop may already be running
    Threads are reused
    External libraries may use asynchronous primitives
    """

    async_to_sync(_create)()

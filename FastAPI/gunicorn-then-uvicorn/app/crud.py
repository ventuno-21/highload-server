from sqlalchemy import select
from app.models import Item
from app.schemas import ItemCreate
from sqlalchemy.ext.asyncio import AsyncSession


async def create_item(db: AsyncSession, item: ItemCreate):
    db_item = Item(**item.model_dump())
    db.add(db_item)
    try:
        await db.commit()
        await db.refresh(db_item)
    except Exception:
        await db.rollback()
        raise
    return db_item


async def list_items(db: AsyncSession, limit: int = 100):
    result = await db.execute(select(Item).limit(limit))
    return result.scalars().all()

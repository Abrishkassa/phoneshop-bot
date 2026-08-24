from sqlalchemy.ext.asyncio import async_session, async_sessionmaker, create_async_engine
from sqlalchemy.orm import DeclarativeBase


from app.core.config import settings

engine = create_async_engine(settings.database_url, echo=False, future=True)
AsyncSessionLocal = async_sessionmaker(engine, expire_on_commit=False, class=AsyncSession)

class Base(DeclarativeBase):
    pass


async def get_db():
    async with AsyncSessionLocal() as session:
        yield session

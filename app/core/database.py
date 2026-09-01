from sqlalchemy.ext.asyncio import AsyncSession, async_sessionmaker, create_async_engine
from sqlalchemy.orm import DeclarativeBase
from sqlalchemy.pool import NullPool

from app.core.config import settings

engine = create_async_engine(
    settings.database_url,
    echo=False,
    future=True,
    # Two SEPARATE caches need disabling for Supabase's PgBouncer transaction
    # pooler: asyncpg's own cache (statement_cache_size) AND SQLAlchemy's
    # own internal prepared-statement cache (prepared_statement_cache_size).
    # Missing the second one is what causes the deterministic
    # "__asyncpg_stmt_1__" name to collide across pooled connections.
    connect_args={
        "statement_cache_size": 0,
        "prepared_statement_cache_size": 0,
        "ssl": "require",
    },
    # NullPool: don't let SQLAlchemy hold and reuse its own raw connections.
    # Supabase's PgBouncer already pools connections underneath — layering
    # SQLAlchemy's pool on top of that is what causes the
    # DuplicatePreparedStatementError when two processes (bot + API) share
    # the same pooled backend connection.
    poolclass=NullPool,
)
AsyncSessionLocal = async_sessionmaker(engine, expire_on_commit=False, class_=AsyncSession)


class Base(DeclarativeBase):
    pass


async def get_db():
    async with AsyncSessionLocal() as session:
        yield session
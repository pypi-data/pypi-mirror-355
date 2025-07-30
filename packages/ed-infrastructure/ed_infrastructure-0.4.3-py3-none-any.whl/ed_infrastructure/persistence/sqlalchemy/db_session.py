from sqlalchemy.ext.asyncio import AsyncSession, async_sessionmaker

from ed_infrastructure.persistence.sqlalchemy.db_engine import DbEngine


class DbSession:
    def __init__(self, db_engine: DbEngine) -> None:
        self._session_factory = async_sessionmaker(
            bind=db_engine.engine,
            autocommit=False,
            autoflush=False,
            expire_on_commit=False,
        )

    def __call__(self) -> AsyncSession:
        return self._session_factory()

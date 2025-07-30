from typing import TypedDict

from sqlalchemy.ext.asyncio import AsyncEngine, create_async_engine


class DbConfig(TypedDict):
    user: str
    password: str
    db: str
    host: str


class DbEngine:
    def __init__(self, config: DbConfig) -> None:
        self._connection_string = f"postgresql+psycopg://{config['user']}:{config['password']}@{config['host']}/{config['db']}"
        self._engine: AsyncEngine = create_async_engine(
            self._connection_string)

    @property
    def engine(self) -> AsyncEngine:
        return self._engine

    def connect(self):
        return self._engine.connect()

    async def dispose(self) -> None:
        await self._engine.dispose()

    def __enter__(self):
        return self

    async def __exit__(self, exc_type, exc_val, exc_tb):
        await self.dispose()

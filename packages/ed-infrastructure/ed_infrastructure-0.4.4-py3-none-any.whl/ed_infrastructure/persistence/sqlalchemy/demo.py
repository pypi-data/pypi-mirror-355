from ed_infrastructure.persistence.sqlalchemy.seed.helpers import get_config
from ed_infrastructure.persistence.sqlalchemy.unit_of_work import UnitOfWork

config = get_config()


async def create_empty_tables():
    uow = UnitOfWork(config)

    await uow.create_tables()


if __name__ == "__main__":
    import asyncio

    asyncio.run(create_empty_tables())

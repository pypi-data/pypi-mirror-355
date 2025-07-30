from abc import abstractmethod
from typing import Any, Generic, Optional, Type, TypeVar
from uuid import UUID

from ed_domain.persistence.async_repositories.abc_async_generic_repository import \
    ABCAsyncGenericRepository
from sqlalchemy import select, update
from sqlalchemy.ext.asyncio import AsyncSession

from ed_infrastructure.persistence.sqlalchemy.models.base_model import \
    BaseModel

TEntity = TypeVar("TEntity")
TModel = TypeVar("TModel", bound=BaseModel)


class AsyncGenericRepository(
    Generic[TEntity, TModel], ABCAsyncGenericRepository[TEntity]
):
    def __init__(self, entity_cls: Type[TModel], session: AsyncSession):
        self._entity_cls = entity_cls
        self._session = session

    @classmethod
    @abstractmethod
    def _to_entity(cls, model: TModel) -> TEntity: ...

    @classmethod
    @abstractmethod
    def _to_model(cls, entity: TEntity) -> TModel: ...

    async def get_all(
        self,
        order_by: Optional[Any] = None,
        limit: Optional[int] = None,
        **filters: Any,
    ) -> list[TEntity]:
        stmt = select(self._entity_cls).filter_by(deleted=False)
        if filters:
            stmt = stmt.filter_by(**filters)
        if order_by is not None:
            stmt = stmt.order_by(order_by)
        if limit is not None:
            stmt = stmt.limit(limit)
        result = await self._session.execute(stmt)
        return list(map(self._to_entity, result.scalars().all()))

    async def get(self, **filters: Any) -> Optional[TEntity]:
        stmt = select(self._entity_cls).filter_by(deleted=False)
        if filters:
            stmt = stmt.filter_by(**filters)
        stmt = stmt.limit(1)
        result = await self._session.execute(stmt)
        if entity := result.scalars().first():
            return self._to_entity(entity)

    async def create(self, entity: TEntity) -> TEntity:
        model = self._to_model(entity)

        self._session.add(model)
        await self._session.flush()
        await self._session.refresh(model)

        return self._to_entity(model)

    async def create_many(self, entities: list[TEntity]) -> list[TEntity]:
        models = [self._to_model(entity) for entity in entities]

        self._session.add_all(models)
        await self._session.flush()
        for model in models:
            await self._session.refresh(model)

        return [self._to_entity(model) for model in models]

    async def update(self, id: UUID, entity: TEntity) -> bool:
        model = self._to_model(entity)
        stmt = (
            update(self._entity_cls)
            .where(self._entity_cls.id == id)
            .values(
                **{
                    k: v
                    for k, v in model.__dict__.items()
                    if not k.startswith("_") and k != "id"
                }
            )
            .returning(self._entity_cls.id)
        )

        result = await self._session.execute(stmt)
        return bool(result.scalar_one_or_none())

    async def delete(self, id: UUID) -> bool:
        stmt = (
            update(self._entity_cls)
            .where(self._entity_cls.id == id)
            .values(deleted=True)
            .returning(self._entity_cls.id)
        )
        result = await self._session.execute(stmt)
        return bool(result.scalar_one_or_none())

    async def save(self, entity: TEntity) -> TEntity:
        orm_model = self._to_model(entity)

        merged_model = await self._session.merge(orm_model)

        merged_entity = self._to_entity(merged_model)

        return merged_entity

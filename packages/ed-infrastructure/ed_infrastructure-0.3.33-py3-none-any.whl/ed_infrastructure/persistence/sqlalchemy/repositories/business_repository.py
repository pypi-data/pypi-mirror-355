from uuid import UUID

from ed_domain.core.aggregate_roots.business import Business
from ed_domain.persistence.async_repositories.abc_async_business_repository import \
    ABCAsyncBusinessRepository

from ed_infrastructure.persistence.sqlalchemy.models import BusinessModel
from ed_infrastructure.persistence.sqlalchemy.repositories.api_key_repository import \
    ApiKeyRepository
from ed_infrastructure.persistence.sqlalchemy.repositories.generic_repository import \
    AsyncGenericRepository


class BusinessRepository(
    ABCAsyncBusinessRepository, AsyncGenericRepository[Business, BusinessModel]
):
    def __init__(self) -> None:
        super().__init__(BusinessModel)
        self._api_key_repository = ApiKeyRepository()

    async def update(self, id: UUID, entity: Business) -> bool:
        api_keys_updated = False
        for api_key in entity.api_keys:
            if await self._api_key_repository.update(api_key.id, api_key):
                api_keys_updated = True

        business_updated = await super().update(id, entity)

        return api_keys_updated or business_updated

    @classmethod
    def _to_entity(cls, model: BusinessModel) -> Business:
        return Business(
            id=model.id,
            user_id=model.user_id,
            business_name=model.business_name,
            owner_first_name=model.owner_first_name,
            owner_last_name=model.owner_last_name,
            phone_number=model.phone_number,
            email=model.email,
            api_keys=[
                ApiKeyRepository._to_entity(api_key) for api_key in model.api_keys
            ],
            location_id=model.location_id,
            create_datetime=model.create_datetime,
            update_datetime=model.update_datetime,
            deleted=model.deleted,
            deleted_datetime=model.deleted_datetime,
        )

    @classmethod
    def _to_model(cls, entity: Business) -> BusinessModel:
        return BusinessModel(
            id=entity.id,
            user_id=entity.user_id,
            business_name=entity.business_name,
            owner_first_name=entity.owner_first_name,
            owner_last_name=entity.owner_last_name,
            phone_number=entity.phone_number,
            email=entity.email,
            location_id=entity.location_id,
            create_datetime=entity.create_datetime,
            update_datetime=entity.update_datetime,
            deleted=entity.deleted,
            deleted_datetime=entity.deleted_datetime,
        )

from ed_domain.core.entities.api_key import ApiKey
from ed_domain.persistence.async_repositories.abc_async_api_key_repository import \
    ABCAsyncApiKeyRepository

from ed_infrastructure.persistence.sqlalchemy.models import ApiKeyModel
from ed_infrastructure.persistence.sqlalchemy.repositories.generic_repository import \
    AsyncGenericRepository


class ApiKeyRepository(
    ABCAsyncApiKeyRepository, AsyncGenericRepository[ApiKey, ApiKeyModel]
):
    def __init__(self) -> None:
        super().__init__(ApiKeyModel)

    @classmethod
    def _to_entity(cls, model: ApiKeyModel) -> ApiKey:
        return ApiKey(
            id=model.id,
            business_id=model.business_id,
            name=model.name,
            description=model.description,
            prefix=model.prefix,
            key_hash=model.key_hash,
            status=model.status,
            create_datetime=model.create_datetime,
            update_datetime=model.update_datetime,
            deleted_datetime=model.update_datetime,
            deleted=model.deleted,
        )

    @classmethod
    def _to_model(cls, entity: ApiKey) -> ApiKeyModel:
        return ApiKeyModel(
            id=entity.id,
            business_id=entity.business_id,
            name=entity.name,
            description=entity.description,
            prefix=entity.prefix,
            key_hash=entity.key_hash,
            status=entity.status,
            create_datetime=entity.create_datetime,
            update_datetime=entity.update_datetime,
            deleted=entity.deleted,
            deleted_datetime=entity.deleted_datetime,
        )

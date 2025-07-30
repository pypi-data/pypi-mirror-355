from ed_domain.core.aggregate_roots.consumer import Consumer
from ed_domain.persistence.async_repositories.abc_async_consumer_repository import \
    ABCAsyncConsumerRepository

from ed_infrastructure.persistence.sqlalchemy.models import ConsumerModel
from ed_infrastructure.persistence.sqlalchemy.repositories.generic_repository import \
    AsyncGenericRepository


class ConsumerRepository(
    ABCAsyncConsumerRepository, AsyncGenericRepository[Consumer, ConsumerModel]
):
    def __init__(self) -> None:
        super().__init__(ConsumerModel)

    @classmethod
    def _to_entity(cls, model: ConsumerModel) -> Consumer:
        return Consumer(
            id=model.id,
            user_id=model.user_id,
            first_name=model.first_name,
            last_name=model.last_name,
            phone_number=model.phone_number,
            profile_image_url=model.profile_image_url,
            email=model.email,
            location_id=model.location_id,
            create_datetime=model.create_datetime,
            update_datetime=model.update_datetime,
            deleted=model.deleted,
            deleted_datetime=model.deleted_datetime,
        )

    @classmethod
    def _to_model(cls, entity: Consumer) -> ConsumerModel:
        return ConsumerModel(
            id=entity.id,
            user_id=entity.user_id,
            first_name=entity.first_name,
            last_name=entity.last_name,
            phone_number=entity.phone_number,
            profile_image_url=entity.profile_image_url,
            email=entity.email,
            location_id=entity.location_id,
            create_datetime=entity.create_datetime,
            update_datetime=entity.update_datetime,
            deleted=entity.deleted,
            deleted_datetime=entity.deleted_datetime,
        )

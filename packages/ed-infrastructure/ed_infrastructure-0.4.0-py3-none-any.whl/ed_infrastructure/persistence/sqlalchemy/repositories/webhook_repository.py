from ed_domain.core.entities.webhook import Webhook
from ed_domain.persistence.async_repositories.abc_async_webhook_repository import \
    ABCAsyncWebHookRepository

from ed_infrastructure.persistence.sqlalchemy.models import WebhookModel
from ed_infrastructure.persistence.sqlalchemy.repositories.generic_repository import \
    AsyncGenericRepository


class WebhookRepository(
    ABCAsyncWebHookRepository, AsyncGenericRepository[Webhook, WebhookModel]
):
    def __init__(self) -> None:
        super().__init__(WebhookModel)

    @classmethod
    def _to_entity(cls, model: WebhookModel) -> Webhook:
        return Webhook(
            id=model.id,
            business_id=model.business_id,
            url=model.url,
            create_datetime=model.create_datetime,
            update_datetime=model.update_datetime,
            deleted_datetime=model.update_datetime,
            deleted=model.deleted,
        )

    @classmethod
    def _to_model(cls, entity: Webhook) -> WebhookModel:
        return WebhookModel(
            id=entity.id,
            business_id=entity.business_id,
            url=entity.url,
            create_datetime=entity.create_datetime,
            update_datetime=entity.update_datetime,
            deleted=entity.deleted,
            deleted_datetime=entity.deleted_datetime,
        )

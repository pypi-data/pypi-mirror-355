from ed_domain.core.entities.notification import Notification
from ed_domain.persistence.async_repositories.abc_async_notification_repository import \
    ABCAsyncNotificationRepository

from ed_infrastructure.persistence.sqlalchemy.models import NotificationModel
from ed_infrastructure.persistence.sqlalchemy.repositories.generic_repository import \
    AsyncGenericRepository


class NotificationRepository(
    ABCAsyncNotificationRepository,
    AsyncGenericRepository[Notification, NotificationModel],
):
    def __init__(self) -> None:
        super().__init__(NotificationModel)

    @classmethod
    def _to_entity(cls, model: NotificationModel) -> Notification:
        return Notification(
            id=model.id,
            user_id=model.user_id,
            notification_type=model.notification_type,
            message=model.message,
            read_status=model.read_status,
            create_datetime=model.create_datetime,
            update_datetime=model.update_datetime,
            deleted=model.deleted,
            deleted_datetime=model.deleted_datetime,
        )

    @classmethod
    def _to_model(cls, entity: Notification) -> NotificationModel:
        return NotificationModel(
            id=entity.id,
            user_id=entity.user_id,
            notification_type=entity.notification_type,
            message=entity.message,
            read_status=entity.read_status,
            create_datetime=entity.create_datetime,
            update_datetime=entity.update_datetime,
            deleted=entity.deleted,
            deleted_datetime=entity.deleted_datetime,
        )

from datetime import UTC, datetime
from uuid import UUID

from ed_domain.core.entities.webhook import Webhook

from ed_infrastructure.common.generic import get_new_id


def get_webhook(business_id: UUID) -> Webhook:
    return Webhook(
        id=get_new_id(),
        url="https://webhook.url",
        business_id=business_id,
        create_datetime=datetime.now(UTC),
        update_datetime=datetime.now(UTC),
        deleted_datetime=None,
        deleted=False,
    )

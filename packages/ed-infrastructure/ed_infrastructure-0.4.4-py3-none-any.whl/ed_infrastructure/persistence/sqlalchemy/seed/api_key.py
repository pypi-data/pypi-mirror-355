from datetime import UTC, datetime
from uuid import UUID

from ed_domain.core.entities.api_key import ApiKey, ApiKeyStatus

from ed_infrastructure.common.generic import get_new_id


def get_api_key(business_id: UUID) -> ApiKey:
    return ApiKey(
        id=get_new_id(),
        name="API Key 1",
        description="Used for connecting website with system.",
        prefix=str(get_new_id())[:8],
        key_hash="$2b$12$mlewRx4nfy7FKCB.RJrVs.N.CD95q3DBBDr6zqxtOzQoBvQjnzFK6",
        status=ApiKeyStatus.ACTIVE,
        business_id=business_id,
        create_datetime=datetime.now(UTC),
        update_datetime=datetime.now(UTC),
        deleted_datetime=datetime.now(UTC),
        deleted=False,
    )

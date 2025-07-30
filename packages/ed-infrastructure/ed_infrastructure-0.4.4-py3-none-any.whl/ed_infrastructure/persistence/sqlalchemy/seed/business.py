from datetime import UTC, datetime
from uuid import UUID

from ed_domain.core.aggregate_roots import Business
from ed_domain.core.entities.api_key import ApiKey

from ed_infrastructure.common.generic import get_new_id


def get_business(
    business_user_id: UUID, location_id: UUID, api_keys: list[ApiKey]
) -> Business:
    return Business(
        user_id=business_user_id,
        id=get_new_id(),
        business_name="Test Business 1",
        owner_first_name="Shamil",
        owner_last_name="Bedru",
        phone_number="251948671563",
        email="shamilbedru47@gmail.com",
        location_id=location_id,
        api_keys=api_keys,
        create_datetime=datetime.now(UTC),
        update_datetime=datetime.now(UTC),
        deleted_datetime=datetime.now(UTC),
        deleted=False,
    )

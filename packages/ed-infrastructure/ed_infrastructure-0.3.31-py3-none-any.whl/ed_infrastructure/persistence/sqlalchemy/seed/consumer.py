from datetime import UTC
from uuid import UUID

from ed_domain.core.aggregate_roots import Consumer
from jsons import datetime

from ed_infrastructure.common.generic import get_new_id


def get_consumer(
    consumer_user_id: UUID,
    location_id: UUID,
    first_name="Fikernew",
    last_name="Birhanu",
    phone_number="251930316620",
    email="phikernew0808@gmail.com",
) -> Consumer:
    return Consumer(
        user_id=consumer_user_id,
        id=get_new_id(),
        first_name=first_name,
        last_name=last_name,
        phone_number=phone_number,
        email=email,
        profile_image_url="",
        location_id=location_id,
        create_datetime=datetime.now(UTC),
        update_datetime=datetime.now(UTC),
        deleted_datetime=datetime.now(UTC),
        deleted=False,
    )

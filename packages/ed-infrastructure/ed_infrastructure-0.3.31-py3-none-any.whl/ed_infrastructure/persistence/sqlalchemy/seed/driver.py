from datetime import UTC
from uuid import UUID

from ed_domain.core.aggregate_roots import Driver
from ed_domain.core.entities import Car
from jsons import datetime

from ed_infrastructure.common.generic import get_new_id


def get_driver(driver_user_id: UUID, car: Car, location_id: UUID) -> Driver:
    return Driver(
        user_id=driver_user_id,
        id=get_new_id(),
        first_name="Firaol",
        last_name="Ibrahim",
        phone_number="251977346620",
        profile_image="",
        car=car,
        email="firaolibrahim28@gmail.com",
        location_id=location_id,
        create_datetime=datetime.now(UTC),
        update_datetime=datetime.now(UTC),
        deleted_datetime=datetime.now(UTC),
        deleted=False,
    )

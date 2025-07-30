from datetime import UTC

from ed_domain.core.entities import Car
from jsons import datetime

from ed_infrastructure.common.generic import get_new_id


def get_car() -> Car:
    return Car(
        id=get_new_id(),
        make="model",
        model="model",
        year=2024,
        registration_number="134141",
        license_plate_number="A30303",
        color="Gold",
        seats=7,
        create_datetime=datetime.now(UTC),
        update_datetime=datetime.now(UTC),
        deleted_datetime=datetime.now(UTC),
        deleted=False,
    )

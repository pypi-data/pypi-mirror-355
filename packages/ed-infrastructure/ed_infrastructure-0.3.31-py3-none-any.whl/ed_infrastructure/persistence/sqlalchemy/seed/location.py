import random
from datetime import UTC

from ed_domain.core.aggregate_roots import Location
from jsons import datetime

from ed_infrastructure.common.generic import get_new_id


def get_location(latitude: float = 8.9, longitude: float = 37.1):
    return Location(
        id=get_new_id(),
        address="Bole Int'l Airport",
        latitude=latitude,
        longitude=longitude,
        postal_code="1000",
        city="Addis Ababa",
        country="Ethiopia",
        last_used=datetime.now(UTC),
        create_datetime=datetime.now(UTC),
        update_datetime=datetime.now(UTC),
        deleted_datetime=datetime.now(UTC),
        deleted=False,
    )


def generate_random_latitude():
    return round(random.uniform(8.90, 9.05), 6)


def generate_random_longitude():
    return round(random.uniform(38.70, 38.85), 6)

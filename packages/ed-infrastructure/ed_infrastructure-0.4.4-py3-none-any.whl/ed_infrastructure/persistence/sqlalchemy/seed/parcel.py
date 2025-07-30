import random
from datetime import UTC, datetime

from ed_domain.core.entities.parcel import Parcel, ParcelSize

from ed_infrastructure.common.generic import get_new_id


def get_parcel() -> Parcel:
    return Parcel(
        id=get_new_id(),
        size=ParcelSize.SMALL,
        length=round(random.uniform(5.0, 50.0), 2),
        width=round(random.uniform(5.0, 50.0), 2),
        height=round(random.uniform(5.0, 50.0), 2),
        weight=round(random.uniform(5.0, 50.0), 2),
        fragile=random.choice([True, False]),
        create_datetime=datetime.now(UTC),
        update_datetime=datetime.now(UTC),
        deleted_datetime=datetime.now(UTC),
        deleted=False,
    )

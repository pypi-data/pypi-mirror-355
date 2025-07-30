from datetime import UTC
from uuid import UUID

from ed_domain.core.aggregate_roots import Order
from ed_domain.core.aggregate_roots.order import OrderStatus
from ed_domain.core.entities import Bill, Parcel
from jsons import datetime, timedelta

from ed_infrastructure.common.generic import get_new_id


def get_order(
    business_id: UUID,
    consumer_id: UUID,
    driver_id: UUID | None,
    bill: Bill,
    parcel: Parcel,
) -> Order:
    return Order(
        id=get_new_id(),
        order_number=str(get_new_id()),
        business_id=business_id,
        consumer_id=consumer_id,
        driver_id=driver_id,
        bill=bill,
        parcel=parcel,
        latest_time_of_delivery=datetime.now(UTC) + timedelta(days=2),
        order_status=OrderStatus.PENDING,
        create_datetime=datetime.now(UTC),
        update_datetime=datetime.now(UTC),
        deleted_datetime=datetime.now(UTC),
        deleted=False,
    )

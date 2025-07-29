import random
from datetime import UTC, datetime, timedelta

from ed_domain.core.entities import Bill
from ed_domain.core.entities.bill import BillStatus

from ed_infrastructure.common.generic import get_new_id


def get_bill() -> Bill:
    return Bill(
        id=get_new_id(),
        amount_in_birr=round(random.uniform(5.0, 100.0), 2),
        bill_status=BillStatus.PENDING,
        due_date=datetime.now(UTC) + timedelta(days=2),
        create_datetime=datetime.now(UTC),
        update_datetime=datetime.now(UTC),
        deleted_datetime=datetime.now(UTC),
        deleted=False,
    )

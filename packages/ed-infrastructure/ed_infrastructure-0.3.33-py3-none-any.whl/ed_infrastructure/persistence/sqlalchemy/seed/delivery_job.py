from datetime import UTC, datetime, timedelta
from uuid import UUID

from ed_domain.core.aggregate_roots import DeliveryJob
from ed_domain.core.aggregate_roots.delivery_job import DeliveryJobStatus
from ed_domain.core.entities.waypoint import Waypoint

from ed_infrastructure.common.generic import get_new_id


def get_delivery_job(driver_id: UUID, waypoints: list[Waypoint]) -> DeliveryJob:
    return DeliveryJob(
        id=get_new_id(),
        driver_id=driver_id,
        waypoints=waypoints,
        estimated_completion_time=datetime.now(UTC) + timedelta(days=2),
        estimated_distance_in_kms=10.2,
        estimated_payment_in_birr=2020,
        estimated_time_in_minutes=10,
        status=DeliveryJobStatus.IN_PROGRESS,
        create_datetime=datetime.now(UTC),
        update_datetime=datetime.now(UTC),
        deleted_datetime=datetime.now(UTC),
        deleted=False,
    )

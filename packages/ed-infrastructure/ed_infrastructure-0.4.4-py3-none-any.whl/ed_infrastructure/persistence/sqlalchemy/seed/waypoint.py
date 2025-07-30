from datetime import UTC, datetime, timedelta
from uuid import UUID

from ed_domain.core.entities.waypoint import (Waypoint, WaypointStatus,
                                              WaypointType)

from ed_infrastructure.common.generic import get_new_id


def get_waypoint(
    delivery_job_id: UUID,
    sequence: int,
    order_id: UUID,
    type: WaypointType = WaypointType.PICK_UP,
) -> Waypoint:
    return Waypoint(
        delivery_job_id=delivery_job_id,
        id=get_new_id(),
        order_id=order_id,
        expected_arrival_time=datetime.now(UTC) + timedelta(days=2),
        actual_arrival_time=datetime.now(UTC) + timedelta(days=2.2),
        sequence=sequence,
        waypoint_type=type,
        waypoint_status=WaypointStatus.PENDING,
        create_datetime=datetime.now(UTC),
        update_datetime=datetime.now(UTC),
        deleted_datetime=datetime.now(UTC),
        deleted=False,
    )

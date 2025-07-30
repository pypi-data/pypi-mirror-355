from uuid import UUID

from ed_domain.core.entities.waypoint import Waypoint, WaypointStatus
from ed_domain.persistence.async_repositories.abc_async_waypoint_repository import \
    ABCAsyncWaypointRepository
from sqlalchemy import update

from ed_infrastructure.persistence.sqlalchemy.models import WaypointModel
from ed_infrastructure.persistence.sqlalchemy.repositories.generic_repository import \
    AsyncGenericRepository


class WaypointRepository(
    ABCAsyncWaypointRepository,
    AsyncGenericRepository[Waypoint, WaypointModel],
):
    def __init__(self) -> None:
        super().__init__(WaypointModel)

    async def update_waypoint_status(self, id: UUID, status: WaypointStatus) -> bool:
        stmt = (
            update(self._entity_cls)
            .where(self._entity_cls.id == id)
            .values(**{"status": status})
            .returning(self._entity_cls.id)
        )

        result = await self._session.execute(stmt)
        return bool(result.scalar_one_or_none())

    @classmethod
    def _to_entity(cls, model: WaypointModel) -> Waypoint:
        return Waypoint(
            id=model.id,
            delivery_job_id=model.delivery_job_id,
            order_id=model.order_id,
            expected_arrival_time=model.expected_arrival_time,
            actual_arrival_time=model.actual_arrival_time,
            sequence=model.sequence,
            waypoint_type=model.waypoint_type,
            waypoint_status=model.waypoint_status,
            create_datetime=model.create_datetime,
            update_datetime=model.update_datetime,
            deleted=model.deleted,
            deleted_datetime=model.deleted_datetime,
        )

    @classmethod
    def _to_model(cls, entity: Waypoint) -> WaypointModel:
        return WaypointModel(
            id=entity.id,
            delivery_job_id=entity.delivery_job_id,
            order_id=entity.order_id,
            expected_arrival_time=entity.expected_arrival_time,
            actual_arrival_time=entity.actual_arrival_time,
            sequence=entity.sequence,
            waypoint_type=entity.waypoint_type,
            waypoint_status=entity.waypoint_status,
            create_datetime=entity.create_datetime,
            update_datetime=entity.update_datetime,
            deleted=entity.deleted,
            deleted_datetime=entity.deleted_datetime,
        )

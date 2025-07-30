from uuid import UUID

from ed_domain.core.aggregate_roots.delivery_job import DeliveryJob
from ed_domain.persistence.async_repositories.abc_async_delivery_job_repository import \
    ABCAsyncDeliveryJobRepository

from ed_infrastructure.persistence.sqlalchemy.models import DeliveryJobModel
from ed_infrastructure.persistence.sqlalchemy.repositories.generic_repository import \
    AsyncGenericRepository
from ed_infrastructure.persistence.sqlalchemy.repositories.waypoint_repository import \
    WaypointRepository


class DeliveryJobRepository(
    ABCAsyncDeliveryJobRepository, AsyncGenericRepository[DeliveryJob,
                                                          DeliveryJobModel]
):
    def __init__(self) -> None:
        super().__init__(DeliveryJobModel)
        self._waypoint_repository = WaypointRepository()

    async def update(self, id: UUID, entity: DeliveryJob) -> bool:
        waypoints_updated = False
        for waypoint in entity.waypoints:
            if await self._waypoint_repository.update(waypoint.id, waypoint):
                waypoints_updated = True

        delivery_job_updated = await super().update(id, entity)

        return waypoints_updated and delivery_job_updated

    @classmethod
    def _to_entity(cls, model: DeliveryJobModel) -> DeliveryJob:
        return DeliveryJob(
            id=model.id,
            driver_id=model.driver_id,
            waypoints=[
                WaypointRepository._to_entity(waypoint) for waypoint in model.waypoints
            ],
            estimated_completion_time=model.estimated_completion_time,
            estimated_distance_in_kms=model.estimated_distance_in_kms,
            estimated_payment_in_birr=model.estimated_payment_in_birr,
            estimated_time_in_minutes=model.estimated_time_in_minutes,
            status=model.status,
            create_datetime=model.create_datetime,
            update_datetime=model.update_datetime,
            deleted=model.deleted,
            deleted_datetime=model.deleted_datetime,
        )

    @classmethod
    def _to_model(cls, entity: DeliveryJob) -> DeliveryJobModel:
        return DeliveryJobModel(
            id=entity.id,
            driver_id=entity.driver_id,
            estimated_completion_time=entity.estimated_completion_time,
            estimated_distance_in_kms=entity.estimated_distance_in_kms,
            estimated_payment_in_birr=entity.estimated_payment_in_birr,
            estimated_time_in_minutes=entity.estimated_time_in_minutes,
            status=entity.status,
            create_datetime=entity.create_datetime,
            update_datetime=entity.update_datetime,
            deleted=entity.deleted,
            deleted_datetime=entity.deleted_datetime,
        )
